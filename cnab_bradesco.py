from decimal import Decimal
import os
import csv

banco = '237'
convenio_oab_rr = '5146161'
convenio_oab_rn = '7926971'
conta_cfoab = '0000000293830'
conta_fida = '0000000293849'
tipo_pagamento = '06'
seguimento_y = 'Y'
seguimento_t = 'T'
seccional_oab_rr = 'OAB/RR'
seccional_oab_rn = 'OAB/RN'

# posições no arquivo CNAB 240
# linha 0
pst_banco = [0, 3]
pst_convenio = [45, 52]
# a partir da linha 3
pst_seguimento = [13, 14]
pst_tipo = [15, 17]
pst_numero_boleto_seg_t = [45, 57]
pst_numero_boleto_seg_y = [47, 59]
pst_conta_recebimento = [85, 98]
pst_valor = [77, 92]
pst_percentual = [61, 73]
pst_data_credito = [145, 153]


def apenas_duas_casas_decimais(vr_ignorar):
    valor_split = str(vr_ignorar).split('.')
    truncado = Decimal(valor_split[0] + '.' + valor_split[1][0:2])
    return truncado


# lista que receberá todos os dados ao final da execução de cada arquivo
lista_final = []

linhas_arquivo = None
pasta = 'import'
# pasta = input('Digite o local dos arquivos: ')
lista_de_arquivos = os.listdir(pasta)
for arquivo_cnab in lista_de_arquivos:
    with open(f'{pasta}/{arquivo_cnab}') as arquivo:
        primeira_linha = arquivo.readline()

        # testando primeira linha para saber se banco e convenio estão cadastrados, caso estejam o
        # restante do arquivo será importado, caso não os sistema informa os dados não cadastrados
        if banco == primeira_linha[pst_banco[0]:pst_banco[1]] \
                and (convenio_oab_rn == primeira_linha[pst_convenio[0]:pst_convenio[1]]
                     or convenio_oab_rr == primeira_linha[pst_convenio[0]:pst_convenio[1]]):

            # colocando cursor no inicio do arquivo
            arquivo.seek(0)
            linhas_arquivo = arquivo.readlines()

        elif banco == primeira_linha[pst_banco[0]:pst_banco[1]] \
                and (not (convenio_oab_rn == primeira_linha[pst_convenio[0]:pst_convenio[1]]
                          or convenio_oab_rr == primeira_linha[pst_convenio[0]:pst_convenio[1]])):
            print(f'Banco cadastrado, mas o convenio {primeira_linha[pst_convenio[0]:pst_convenio[1]]}'
                  f' não está cadastrado.')
        else:
            print(f'O Banco "{primeira_linha[pst_banco[0]:pst_banco[1]]}"'
                  f' e o convenio "{primeira_linha[pst_convenio[0]:pst_convenio[1]]}" não está cadastrado.')

    if linhas_arquivo is not None:
        titulos_validos = []
        # Montagem de lista com todos os seguimentos Y que contenham as contas cadastradas
        for idx, linha in enumerate(linhas_arquivo):
            if linhas_arquivo[idx][pst_tipo[0]:pst_tipo[1]] == tipo_pagamento \
                    and linhas_arquivo[idx][pst_seguimento[0]:pst_seguimento[1]] == seguimento_y:
                # and ((linhas_arquivo[idx][pst_conta_recebimento[0]:pst_conta_recebimento[1]] == conta_cfoab)
                #     or (linhas_arquivo[idx][pst_conta_recebimento[0]:pst_conta_recebimento[1]] == conta_fida)):
                conta_recebimento = linhas_arquivo[idx][pst_conta_recebimento[0]:pst_conta_recebimento[1]]
                nosso_numero_y = linhas_arquivo[idx][pst_numero_boleto_seg_y[0]:pst_numero_boleto_seg_y[1]]
                percentual = (Decimal(linhas_arquivo[idx][pst_percentual[0]:pst_percentual[1]])) / 100

                # Teste para verificar se é a ultima rateio do bloco de seguimento y
                if linhas_arquivo[idx + 1][pst_seguimento[0]:pst_seguimento[1]] == seguimento_t:
                    ultimo_rateio = True
                else:
                    ultimo_rateio = False

                # Teste para criação variavel seccional
                if convenio_oab_rn == primeira_linha[pst_convenio[0]:pst_convenio[1]]:
                    seccional = seccional_oab_rn
                elif convenio_oab_rr == primeira_linha[pst_convenio[0]:pst_convenio[1]]:
                    seccional = seccional_oab_rr

                item = {'conta': conta_recebimento, 'numero': nosso_numero_y, 'valor': 0,
                        'percentual': percentual, 'data': 'data_credito', 'seccional': seccional,
                        'ultimo_rateio': ultimo_rateio}
                titulos_validos.append(item)

        # Criando dicionario idexado pelo nosso numero com dados de valor e data de credito
        dicionario_titulos_tipo_06 = {}
        for idx, linha in enumerate(linhas_arquivo):
            if linhas_arquivo[idx][pst_tipo[0]:pst_tipo[1]] == tipo_pagamento \
                    and linhas_arquivo[idx][pst_seguimento[0]:pst_seguimento[1]] == seguimento_t:
                nosso_numero_t = linhas_arquivo[idx][pst_numero_boleto_seg_t[0]:pst_numero_boleto_seg_t[1]]
                valor = Decimal(linhas_arquivo[idx + 1][pst_valor[0]:pst_valor[1]]) / 100
                data_credito = linhas_arquivo[idx + 1][pst_data_credito[0]:pst_data_credito[1]]
                # Formatando data de credito
                data_credito = data_credito[0:2] + '/' + data_credito[2:4] + '/' + data_credito[4:8]
                item = {'valor': valor, 'data': data_credito}
                dicionario_titulos_tipo_06[nosso_numero_t] = item

        # Calculando valor de rateio e inserindo os valores de data, valor titulo e valor rateio
        # nos respectivos nosso numero na lista titulos_validos
        for idx, linha in enumerate(titulos_validos):
            if titulos_validos[idx].get('numero') in dicionario_titulos_tipo_06:
                titulos_validos[idx]['data'] = dicionario_titulos_tipo_06[titulos_validos[idx].get('numero')].get('data')
                valor = dicionario_titulos_tipo_06[titulos_validos[idx].get('numero')].get('valor')
                percentual = titulos_validos[idx].get('percentual')
                valor_calculado = apenas_duas_casas_decimais(valor * percentual)
                # Adicionado valores na lista
                titulos_validos[idx]['valor'] = valor
                titulos_validos[idx]['valor_calculado'] = valor_calculado

                # verificando resto arredondamento
                if titulos_validos[idx].get('ultimo_rateio'):
                    # Criação e preenchimento de lista para calculo diferença de rateio
                    lista_diferenca_rateio = {'soma_percentual': 0, 'soma_rateio': 0, 'vr_titulo': 0}
                    for i, l in enumerate(titulos_validos):
                        if titulos_validos[idx].get('numero') == titulos_validos[i].get('numero'):
                            lista_diferenca_rateio['soma_percentual'] += titulos_validos[i].get('percentual')
                            lista_diferenca_rateio['soma_rateio'] += titulos_validos[i].get('valor_calculado')
                            lista_diferenca_rateio['vr_titulo'] = titulos_validos[i].get('valor')
                    # Calculado diferença de rateio a partir da lista de soma
                    vr_rateio = lista_diferenca_rateio['soma_percentual'] * lista_diferenca_rateio['vr_titulo']
                    vr_rateio = apenas_duas_casas_decimais(vr_rateio)
                    soma_rateio = apenas_duas_casas_decimais(lista_diferenca_rateio['soma_rateio'])
                    # arredondamento desativado, somente assim funcionou corretamente até agora.
                    # diferenca_rateio = apenas_duas_casas_decimais(vr_rateio - soma_rateio)
                    diferenca_rateio = vr_rateio - soma_rateio
                    # Adicionando diferença na lista de titulos validos no item marcado como True para ultimo rateio
                    titulos_validos[idx]['diferenca_rateio'] = diferenca_rateio
                else:
                    titulos_validos[idx]['diferenca_rateio'] = 0

            # impressao de cada dado coletado
            # print(f'indice: {idx}, linha: {linha}')

        dicionario_soma_cfoab = {}
        dicionario_soma_fida = {}

        for idx, linha in enumerate(titulos_validos):
            if titulos_validos[idx].get('conta') == conta_cfoab and len(dicionario_soma_cfoab) == 0:
                valor_calculado = titulos_validos[idx].get('valor_calculado') + titulos_validos[idx].get('diferenca_rateio')
                data_credito = titulos_validos[idx].get('data')
                seccional = titulos_validos[idx].get('seccional')
                chave_dicionario = (seccional, data_credito)
                dicionario_soma_cfoab[chave_dicionario] = valor_calculado

            elif titulos_validos[idx].get('conta') == conta_cfoab and len(dicionario_soma_cfoab) > 0:
                valor_calculado = titulos_validos[idx].get('valor_calculado') + titulos_validos[idx].get('diferenca_rateio')
                data_credito = titulos_validos[idx].get('data')
                seccional = titulos_validos[idx].get('seccional')
                chave_dicionario = (seccional, data_credito)
                valor_soma = dicionario_soma_cfoab[chave_dicionario] + valor_calculado
                dicionario_soma_cfoab[chave_dicionario] = valor_soma

            elif titulos_validos[idx].get('conta') == conta_fida and len(dicionario_soma_fida) == 0:
                valor_calculado = titulos_validos[idx].get('valor_calculado') + titulos_validos[idx].get('diferenca_rateio')
                data_credito = titulos_validos[idx].get('data')
                seccional = titulos_validos[idx].get('seccional')
                chave_dicionario = (seccional, data_credito)
                dicionario_soma_fida[chave_dicionario] = valor_calculado

            elif titulos_validos[idx].get('conta') == conta_fida and len(dicionario_soma_fida) > 0:
                valor_calculado = titulos_validos[idx].get('valor_calculado') + titulos_validos[idx].get('diferenca_rateio')
                data_credito = titulos_validos[idx].get('data')
                seccional = titulos_validos[idx].get('seccional')
                chave_dicionario = (seccional, data_credito)
                valor_soma = dicionario_soma_fida[chave_dicionario] + valor_calculado
                dicionario_soma_fida[chave_dicionario] = valor_soma

        for chave, valor in dicionario_soma_cfoab.items():
            result1, result2 = chave
            # O valor final está sendo arredondado em 2 casa decimais
            result3 = valor
            tupla_resultados_finais = ('CFOAB', result2, result1, result3)
            lista_final.append(tupla_resultados_finais)
            # prin(tupla_resultados_finais)
            # print(f'CFOAB - {chave} - Valor R$ {valor:.2f} ')

        for chave, valor in dicionario_soma_fida.items():
            result1, result2 = chave
            # O valor final está sendo arredondado em 2 casa decimais
            result3 = valor
            tupla_resultados_finais = ('FIDA', result2, result1, result3)
            lista_final.append(tupla_resultados_finais)
            # print(tupla_resultados_finais)
            # print(f' FIDA - {chave} - Valor R$ {valor:.2f} ')

# print(lista_final)
arquivo = 'retorno/tabela.csv'
with open(arquivo, 'w', newline='') as arquivo_csv:
    escritor = csv.writer(arquivo_csv, delimiter=';')
    escritor.writerow(('CONTA', 'DATA', 'SECCIONAL', 'VALOR'))
    for item in lista_final:
        # Convertendo valor para string
        valor_str = str(item[3])
        # Substituindo ponto por virgula
        valor_str = valor_str.replace('.', ',')
        # Criando tupla a ser escrita, já que tuplas de origem não pode ser manipulada
        tupla_escrita = (item[0], item[1], item[2], valor_str)
        escritor.writerow(tupla_escrita)

datas_oab_rr = []
datas_oab_rn = []
lista_titulos_convenio5146_cfoab = []
lista_titulos_convenio5147_fida = []
lista_titulos_convenio7926_cfoab = []
lista_titulos_convenio7927_fida = []
for conta, data, seccional, valor in lista_final:
    if seccional == 'OAB/RR' and conta == 'CFOAB':
        # Removendo formatação data de credito
        data = data[0:2] + data[3:5] + data[6:10]
        # Calculando valor ref 10% a lançar no cnab e convertendo em string
        valor = int(((valor * 100) / 10) * 100)
        valor = str(valor)
        dados = (data, valor)
        lista_titulos_convenio5146_cfoab.append(dados)
        # Criando lista de datas para calcular maior e menor
        data = int(data)
        datas_oab_rr.append(data)
    elif seccional == 'OAB/RR' and conta == 'FIDA':
        # Removendo formatação data de credito
        data = data[0:2] + data[3:5] + data[6:10]
        # Calculando valor ref 2% a lançar no cnab e convertendo em string
        valor = int(((valor * 100) / 2) * 100)
        valor = str(valor)
        dados = (data, valor)
        lista_titulos_convenio5147_fida.append(dados)
    elif seccional == 'OAB/RN' and conta == 'CFOAB':
        # Removendo formatação data de credito
        data = data[0:2] + data[3:5] + data[6:10]
        # Calculando valor ref 10% a lançar no cnab e convertendo em string
        valor = int(((valor * 100) / 10) * 100)
        valor = str(valor)
        dados = (data, valor)
        lista_titulos_convenio7926_cfoab.append(dados)
        # Criando lista de datas para calcular maior e menor
        data = int(data)
        datas_oab_rn.append(data)
    elif seccional == 'OAB/RN' and conta == 'FIDA':
        # Removendo formatação data de credito
        data = data[0:2] + data[3:5] + data[6:10]
        # Calculando valor ref 2% a lançar no cnab e convertendo em string
        valor = int(((valor * 100) / 2) * 100)
        valor = str(valor)
        dados = (data, valor)
        lista_titulos_convenio7927_fida.append(dados)


def criar_arquivo_cnab(nome_seccional, convenio, data_inicial, data_final, lista_dados):
    # adicionando 0 a esquerda para completar 8 digitos
    data_inicial = (str(data_inicial)).zfill(8)
    data_final = (str(data_final)).zfill(8)

    cnab = f'retorno/{nome_seccional}-{convenio}_{data_inicial}_a_{data_final}.ret'
    with open(cnab, 'w') as cnab:
        cnab.write(
            f'23700000         2084510640001100000000000000{convenio}97102173300000001086855ORDEM DOS ADVOGADOS'
            ' DO BRASILSBRADESCO                                20301202004171800049908301600           '
            '                             00000                        \n')
        cnab.write('23700011T01  042 20084510640001100000000000000792697102173300000001086855ORDEM DOS ADVOGADO'
                      'S DO BRASILS                                                                               '
                      ' 000004990201202003012020                                 \n')
        for data_cred, valor_cred in lista_dados:
            # adicionando 0 a esquerda para completar 15 digitos
            valor_cred = valor_cred.zfill(15)

            cnab.write('2370001301401T 0602173300000001086855009     000035955197100000000359551930122019000000'
                          '0000018130010385300000000000000000003595519001524038234000049                          '
                          '              00000000000000000000000000000000000                 \n')
            cnab.write(f'2370001301402U 06000000000000036000000000000000000000000000000000000000000000'
                          f'{valor_cred}00000000000000000000000000000000000000000000001012020'
                          f'{data_cred}            000000000000000                              000    '
                          f'                00     \n')

        cnab.write('23700015         00154400030900000000006845810000000000000000000000000000000000000000000000'
                      '00000000000000000000000000000499                                                           '
                      '                                                          \n')
        cnab.write('23799999         000001001546000000                                                        '
                      '                                                                                           '
                      '                                                          ')


if len(lista_titulos_convenio5146_cfoab) > 0:
    nome = 'OABRR'
    cod = '5146'
    data_ini = min(datas_oab_rr)
    data_fin = max(datas_oab_rr)
    criar_arquivo_cnab(nome, cod, data_ini, data_fin, lista_titulos_convenio5146_cfoab)
    print(lista_titulos_convenio5146_cfoab)

if len(lista_titulos_convenio5147_fida) > 0:
    nome = 'OABRR'
    cod = '5147'
    data_ini = min(datas_oab_rr)
    data_fin = max(datas_oab_rr)
    criar_arquivo_cnab(nome, cod, data_ini, data_fin, lista_titulos_convenio5147_fida)
    print(lista_titulos_convenio5147_fida)

if len(lista_titulos_convenio7926_cfoab) > 0:
    nome = 'OABRN'
    cod = '7926'
    data_ini = min(datas_oab_rn)
    data_fin = max(datas_oab_rn)
    criar_arquivo_cnab(nome, cod, data_ini, data_fin, lista_titulos_convenio7926_cfoab)
    print(lista_titulos_convenio7926_cfoab)

if len(lista_titulos_convenio7927_fida) > 0:
    nome = 'OABRN'
    cod = '7927'
    data_ini = min(datas_oab_rn)
    data_fin = max(datas_oab_rn)
    criar_arquivo_cnab(nome, cod, data_ini, data_fin, lista_titulos_convenio7927_fida)
    print(lista_titulos_convenio7927_fida)

print(f'O arquivo retorno com os dados dos arquivos foi criado no seguinte local: {arquivo}')
