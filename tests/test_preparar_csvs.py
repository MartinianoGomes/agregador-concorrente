from scripts.preparar_csvs import indice_posto


def test_mesmo_cnpj_retorna_mesmo_posto():
    cnpj = "01.492.748/0003-83"

    primeiro = indice_posto(cnpj)
    segundo = indice_posto("01492748000383")

    assert primeiro == segundo


def test_indice_dentro_do_intervalo():
    resultado = indice_posto("01.492.748/0003-83")

    assert 0 <= resultado < 4


def test_cnpjs_diferentes_geram_indices_validos():
    cnpjs = [
        "01.492.748/0003-83",
        "12.345.678/0001-90",
        "98.765.432/0001-10",
    ]

    for cnpj in cnpjs:
        resultado = indice_posto(cnpj)

        assert 0 <= resultado < 4