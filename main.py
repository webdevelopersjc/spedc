from util import f_monta_hirarquia_efd_c
from util import ler_diretorio_txt
from util import mapear_efd_c
from util import converte_para_valor

import pandas as pd
from datetime import datetime

"""
pip install pandas
pip install openpyxl
"""
diretorio = 'C:/VALBAGS/OneDrive - De Biasi Consultoria Tributária S S/CBRS/EFD-Contribuições/2017/'
start = datetime.now()
print("Mapeando diretório com TXT")
lst_txt_dir = ler_diretorio_txt('./sped/')  # Diretório de leitura
dic_nivel_efd_c = f_monta_hirarquia_efd_c('hirarquia_efd_c.txt')  # arquivo de hierarquia - NÃO ALTERAR
dic_selic = f_monta_hirarquia_efd_c('selic.txt',
                                    False)  # Tabela SELIC para calculo de Juros - Atualizar no mes corrente via EXCEL

dic_xls = {}  # Saída de Dados
lst_cfop = ["5101", "5115", "1201", "5102", "5116", "1202", "5103", "5117", "1203", "5104", "5118", "1204", "5105",
            "5119", "1410", "5106", "5120", "1411", "5107", "5122", "5109", "5123", "5110", "5401", "5111", "5402",
            "5112", "5403", "5113", "5405", "5114"]  # filtro CFOP

"""
INDICE ZERO(0) SERÁ PAI DO REGISTRO
DIC[CNPJ_DATA_REF][REGISTRO][LINHA][R][LISTA DOS CAMPOS IGUAL EFD] - REGISTRO 
DIC[CNPJ_DATA_REF][REGISTRO][LINHA][F][REGISTRO FILHO][LISTA DE NUMEROS DE LINHAS DOS FILHOS] - FILHOS
"""
# 1635004
reg = 'C010'  # PARA FILTRAR O CNPJ DO AM
reg_filho = 'C100'
reg_neto = 'C170'  # FALTA FILTROS DO CFOP

for txt in lst_txt_dir:
    print("Lendo TXT:", txt)
    dic_efd_c, lst_filtro_am, lst_filtro_ibge = mapear_efd_c(txt, dic_nivel_efd_c)
    print("Tempo do Arquivo: ", datetime.now() - start)
    for cnpj_data_ref in dic_efd_c:
        cnpj, data_ref = cnpj_data_ref.split('|')
        if reg in dic_efd_c[cnpj_data_ref]:
            for id in dic_efd_c[cnpj_data_ref][reg]:
                #cnpj_c010 = dic_efd_c[cnpj_data_ref][reg][id]['R'][2]


                # para filtrar cnpj constante na tabela filtrada no "util.py" do AM
                if reg_filho in dic_efd_c[cnpj_data_ref][reg][id]['F']:
                    for id_filho in dic_efd_c[cnpj_data_ref][reg][id]['F'][reg_filho]:
                        indemit_c100 = dic_efd_c[cnpj_data_ref][reg_filho][id_filho]['R'][3]
                        codpart_c100 = dic_efd_c[cnpj_data_ref][reg_filho][id_filho]['R'][4]
                        if indemit_c100 == '0' and codpart_c100 in lst_filtro_ibge:
                            for id_neto in dic_efd_c[cnpj_data_ref][reg_filho][id_filho]['F'][reg_neto]:
                                ls = dic_efd_c[cnpj_data_ref][reg_neto][id_neto]['R']
                                cfop = ls[11]
                                # checa lista de CFOP e faz os calculos
                                if cfop in lst_cfop:
                                    vl_icms = converte_para_valor(ls[15])
                                    alq_pis = converte_para_valor(ls[27]) / 100
                                    vl_pis = round(vl_icms * alq_pis, 2) if vl_icms > 0 else 0
                                    alq_cofins = converte_para_valor(ls[33]) / 100
                                    vl_cofins = round(vl_icms * alq_cofins, 2) if vl_icms > 0 else 0
                                    # para criar a estrutura de saída
                                    if cnpj_data_ref not in dic_xls:
                                        "cnpj,data_ref, vl_icms, vl_pis, vl_cofins,calc_juros_pis,calc_juros_cofins,"
                                        dic_xls[cnpj_data_ref] = [cnpj, data_ref, 0, 0, 0, 0, 0, 0, 0]

                                    calc_juros_cofins = round(vl_cofins * dic_selic[data_ref][1] / 100, 2)
                                    calc_juros_pis = round(vl_pis * dic_selic[data_ref][1] / 100, 2)

                                    dic_xls[cnpj_data_ref][2] += vl_icms
                                    dic_xls[cnpj_data_ref][3] += vl_pis
                                    dic_xls[cnpj_data_ref][4] += vl_cofins
                                    dic_xls[cnpj_data_ref][5] += calc_juros_pis
                                    dic_xls[cnpj_data_ref][6] += calc_juros_cofins
                                    dic_xls[cnpj_data_ref][7] += vl_pis + calc_juros_pis
                                    dic_xls[cnpj_data_ref][8] += vl_cofins + calc_juros_cofins

    dic_efd_c.clear()
    print("Tempo do Arquivo: ", datetime.now() - start)

filename = "./relatorio.xlsx"
data = pd.DataFrame.from_dict(dic_xls, orient='index',
                              columns=["cnpj", "data_ref", "vl_icms", "vl_pis",
                                       "vl_cofins",
                                       "calc_juros_pis", "calc_juros_cofins",
                                       "Soma Pis+Juros",
                                       "Soma Cofins + Juros"])
data.to_excel(filename)

print("Tempo total de processamento: ", datetime.now() - start)
print('fim')