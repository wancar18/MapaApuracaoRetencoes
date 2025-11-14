# test_rules_engine.py
import unittest
import pandas as pd
from unittest.mock import MagicMock

# The module to be tested
import rules_engine

class TestFiscalRulesEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up mock data once for all tests."""
        cnae_data = {
            'cnae': [6204000, 6201501],
            'descricao': ['Consultoria em TI', 'Desenvolvimento de software'],
            'anexo': ['V', 'IV'],
            'retencao': ['NAO', 'SIM'],
            'art219': ['', 'Art. 219...']
        }
        reinf_data = {'codigo': [15032], 'descricao': ['Serviços de programação']}
        lc116_data = {"1.07": "Suporte Técnico", "3.01": "Serviço de Cessão de Mão de Obra"}

        cls.mock_rules = {
            'cnae': pd.DataFrame(cnae_data),
            'reinf': pd.DataFrame(reinf_data),
            'lc116': lc116_data
        }

        # This is the default mock state, save it to restore after tests.
        cls.default_cnae_mock = {"codigo": "6204000", "descricao": "Consultoria em TI", "anexo": "V", "retencao": "NAO", "art219": ""}

        # Mocking the consensus functions to isolate the calculation logic
        rules_engine.escolher_lc116_com_consenso = MagicMock(return_value={"codigo": "1.07", "descricao": "Suporte Técnico"})
        rules_engine.escolher_cnae_com_consenso = MagicMock(return_value=cls.default_cnae_mock)
        rules_engine.escolher_reinf_com_consenso = MagicMock(return_value={"codigo": "15032", "descricao": "Serviços de programação"})
        rules_engine.buscar_aliquota_iss = MagicMock(return_value=0.05)


    def setUp(self):
        """Set up data for each individual test."""
        self.dados_nf = {
            'valor_total': 1000.0,
            'municipio_prestador': 'SAO PAULO',
            'municipio_tomador': 'SAO PAULO',
        }
        self.user_config = {
            'nome_unidade': 'TESTE',
            'substituto_tributario': True,
            'possui_cebas': False,
        }
        self.texto_nota = "Sample note text"
        # Ensure the mock is reset before each test
        rules_engine.escolher_cnae_com_consenso.return_value = self.default_cnae_mock

    def test_iss_retention_same_city_substituto(self):
        """Test ISS retention when service is in the same city and taker is substituto."""
        simples = {'is_optante_simples': True, 'is_simei': False}
        result = rules_engine.processar_regras_fiscais(self.dados_nf, simples, self.user_config, self.mock_rules, self.texto_nota)
        self.assertAlmostEqual(result['valor_iss_retido'], 50.0) # 1000 * 5%
        self.assertTrue(any("substituto tributário" in s for s in result['observacoes_legais']))

    def test_iss_no_retention_for_simei(self):
        """Test that ISS is not retained for SIMEI providers."""
        simples = {'is_optante_simples': True, 'is_simei': True}
        result = rules_engine.processar_regras_fiscais(self.dados_nf, simples, self.user_config, self.mock_rules, self.texto_nota)
        self.assertEqual(result['valor_iss_retido'], 0)
        self.assertTrue(any("fornecedor SIMEI" in s for s in result['observacoes_legais']))

    def test_inss_retention_anexo_iv(self):
        """Test INSS retention for Simples Nacional, Anexo IV services."""
        simples = {'is_optante_simples': True, 'is_simei': False}
        # Override the mock for this specific test with a COMPLETE dictionary
        rules_engine.escolher_cnae_com_consenso.return_value = {
            "codigo": "6201501",
            "descricao": "Desenvolvimento de software",
            "anexo": "IV",
            "retencao": "SIM",
            "art219": "Art. 219..."
        }
        result = rules_engine.processar_regras_fiscais(self.dados_nf, simples, self.user_config, self.mock_rules, self.texto_nota)
        self.assertAlmostEqual(result['valor_inss_retido'], 110.0) # 1000 * 11%
        self.assertTrue(any("Anexo IV" in s for s in result['observacoes_legais']))

    def test_inss_no_retention_outside_anexo_iv(self):
        """Test no INSS retention for Simples Nacional services outside Anexo IV."""
        simples = {'is_optante_simples': True, 'is_simei': False}
        result = rules_engine.processar_regras_fiscais(self.dados_nf, simples, self.user_config, self.mock_rules, self.texto_nota)
        self.assertEqual(result['valor_inss_retido'], 0)
        self.assertTrue(any("fora das regras" in s for s in result['observacoes_legais']))

    def test_triage_non_optante_not_exception(self):
        """Test that a non-optante service not in the exception list returns None."""
        simples = {'is_optante_simples': False, 'is_simei': False}
        # The default mock for LC 116 is 1.07, which is not in the exception list
        result = rules_engine.processar_regras_fiscais(self.dados_nf, simples, self.user_config, self.mock_rules, self.texto_nota)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
