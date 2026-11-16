from src.posto import carregar_base_precos


def test_carregar_preco_do_csv(tmp_path):
    arquivo = tmp_path / "posto.csv"

    arquivo.write_text(
        "Estado - Sigla;Municipio;Produto;Valor de Venda;Data da Coleta;CNPJ da Revenda\n"
        "PA;BELEM;GASOLINA;6,29;10/06/2026;01.492.748/0003-83\n",
        encoding="utf-8",
    )

    base = carregar_base_precos(arquivo)

    assert base[("PA", "belem", "gasolina_comum")] == 6.29


def test_prioriza_coleta_mais_recente(tmp_path):
    arquivo = tmp_path / "posto.csv"

    arquivo.write_text(
        "Estado - Sigla;Municipio;Produto;Valor de Venda;Data da Coleta;CNPJ da Revenda\n"
        "PA;BELEM;GASOLINA;6,50;20/06/2026;01.492.748/0003-83\n"
        "PA;BELEM;GASOLINA;6,10;10/01/2026;01.492.748/0003-83\n",
        encoding="utf-8",
    )

    base = carregar_base_precos(arquivo)

    assert base[("PA", "belem", "gasolina_comum")] == 6.50


def test_menor_preco_entre_ultimas_coletas(tmp_path):
    arquivo = tmp_path / "posto.csv"

    arquivo.write_text(
        "Estado - Sigla;Municipio;Produto;Valor de Venda;Data da Coleta;CNPJ da Revenda\n"
        "PA;BELEM;GASOLINA;5,90;10/01/2026;11111111000111\n"
        "PA;BELEM;GASOLINA;6,50;20/06/2026;11111111000111\n"
        "PA;BELEM;GASOLINA;6,30;15/06/2026;22222222000122\n",
        encoding="utf-8",
    )

    base = carregar_base_precos(arquivo)

    assert base[("PA", "belem", "gasolina_comum")] == 6.30


def test_ignora_registro_com_preco_invalido(tmp_path):
    arquivo = tmp_path / "posto.csv"

    arquivo.write_text(
        "Estado - Sigla;Municipio;Produto;Valor de Venda;Data da Coleta;CNPJ da Revenda\n"
        "PA;BELEM;GASOLINA;;10/06/2026;11111111000111\n"
        "PA;BELEM;GASOLINA;6,29;10/06/2026;22222222000122\n",
        encoding="utf-8",
    )

    base = carregar_base_precos(arquivo)

    assert base[("PA", "belem", "gasolina_comum")] == 6.29



def test_mesma_cidade_em_estados_diferentes_nao_se_misturam(tmp_path):
    """Municípios homônimos (ex.: Santa Rosa existe em vários estados) ficam separados."""
    arquivo = tmp_path / "posto.csv"

    arquivo.write_text(
        "Estado - Sigla;Municipio;Produto;Valor de Venda;Data da Coleta;CNPJ da Revenda\n"
        "PA;SANTA ROSA;GASOLINA;6,10;10/06/2026;11111111000111\n"
        "TO;SANTA ROSA;GASOLINA;6,90;10/06/2026;22222222000122\n",
        encoding="utf-8",
    )

    base = carregar_base_precos(arquivo)

    assert base[("PA", "santa rosa", "gasolina_comum")] == 6.10
    assert base[("TO", "santa rosa", "gasolina_comum")] == 6.90


def test_aceita_csv_com_bom(tmp_path):
    arquivo = tmp_path / "posto.csv"

    arquivo.write_text(
        "Estado - Sigla;Municipio;Produto;Valor de Venda;Data da Coleta;CNPJ da Revenda\n"
        "PA;BELÉM;GASOLINA;6,29;10/06/2026;11111111000111\n",
        encoding="utf-8-sig",
    )

    base = carregar_base_precos(arquivo)

    assert base[("PA", "belem", "gasolina_comum")] == 6.29
