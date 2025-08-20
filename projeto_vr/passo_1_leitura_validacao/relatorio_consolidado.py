#!/usr/bin/env python3
# relatorio_consolidado.py

import json
import sys
from datetime import datetime


def gerar_relatorio_detalhado(caminho_json: str):
    """Gera um relatório detalhado a partir do JSON consolidado."""

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Arquivo {caminho_json} não encontrado!")
        print("Execute 'make json-consolidado' primeiro.")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return

    print("=" * 80)
    print("🏢 RELATÓRIO CONSOLIDADO DE RECURSOS HUMANOS - VALE REFEIÇÃO")
    print("=" * 80)

    # Metadata
    metadata = data.get("metadata", {})
    print(f"📅 Data do processamento: {metadata.get('data_processamento', 'N/A')}")
    print(f"🔢 Versão: {metadata.get('versao', 'N/A')}")
    print(f"📋 Descrição: {metadata.get('descricao', 'N/A')}")

    # Estatísticas gerais
    stats = data.get("estatisticas", {})
    print(f"\n📊 ESTATÍSTICAS GERAIS")
    print("-" * 40)
    print(f"👥 Total de colaboradores: {stats.get('total_colaboradores', 0):,}")
    print(
        f"✅ Ativos: {stats.get('ativos', 0):,} ({stats.get('ativos', 0)/stats.get('total_colaboradores', 1)*100:.1f}%)"
    )
    print(
        f"🚪 Desligados: {stats.get('desligados', 0):,} ({stats.get('desligados', 0)/stats.get('total_colaboradores', 1)*100:.1f}%)"
    )
    print(
        f"🆕 Admitidos no mês: {stats.get('admitidos_mes', 0):,} ({stats.get('admitidos_mes', 0)/stats.get('total_colaboradores', 1)*100:.1f}%)"
    )
    print(
        f"🏖️  Em férias: {stats.get('em_ferias', 0):,} ({stats.get('em_ferias', 0)/stats.get('total_colaboradores', 1)*100:.1f}%)"
    )
    print(f"🏛️  Total de sindicatos: {stats.get('total_sindicatos', 0)}")
    print(f"🗺️  Total de estados: {stats.get('total_estados', 0)}")

    # Sindicatos
    sindicatos = data.get("sindicatos", {})
    print(f"\n🏛️  SINDICATOS E DISTRIBUIÇÃO")
    print("-" * 60)
    for nome, info in sorted(
        sindicatos.items(), key=lambda x: x[1]["colaboradores_count"], reverse=True
    ):
        nome_curto = nome[:50] + "..." if len(nome) > 50 else nome
        colaboradores = info.get("colaboradores_count", 0)
        dias_uteis = info.get("dias_uteis", 0)
        percentual = colaboradores / stats.get("total_colaboradores", 1) * 100
        print(f"📍 {nome_curto}")
        print(f"   👥 Colaboradores: {colaboradores:,} ({percentual:.1f}%)")
        print(f"   📅 Dias úteis: {dias_uteis}")
        print()

    # Valores por estado
    valores_estado = data.get("valores_por_estado", {})
    print(f"💰 VALORES DE VALE REFEIÇÃO POR ESTADO")
    print("-" * 50)
    for estado, valor in sorted(valores_estado.items()):
        if estado and str(valor).lower() != "nan":
            print(f"🗺️  {estado}: R$ {valor:.2f}")

    # Análise por status
    colaboradores = data.get("colaboradores", {})
    status_count = {}

    for colaborador in colaboradores.values():
        status = colaborador.get("status", "indefinido")
        status_count[status] = status_count.get(status, 0) + 1

    print(f"\n📊 DISTRIBUIÇÃO POR STATUS")
    print("-" * 40)
    for status, count in sorted(status_count.items(), key=lambda x: x[1], reverse=True):
        percentual = count / len(colaboradores) * 100 if colaboradores else 0
        print(f"🏷️  {status.title()}: {count:,} ({percentual:.1f}%)")

    print("\n" + "=" * 80)
    print("✅ Relatório gerado com sucesso!")
    print(
        "💡 Para mais detalhes, consulte o arquivo JSON completo em ./output/base_consolidada.json"
    )
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        caminho_json = sys.argv[1]
    else:
        caminho_json = "./output/base_consolidada.json"

    gerar_relatorio_detalhado(caminho_json)
