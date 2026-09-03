# CeraForm - Reconstituição geométrica de cerâmicas
# Copyright (c) 2026 Claudia Alves de Oliveira & Luis Antonio da Silva
# SPDX-License-Identifier: LicenseRef-CeraForm-Academic-NC

from __future__ import annotations

FORMAS = (
    "Carenado",
    "Carenado Duplo",
    "Cilíndrico",
    "Cônico",
    "Bicônico (Cone Duplo)",
    "Discoide",
    "Escalonado",
    "Esférico",
    "Elipsóide Vertical",
    "Elipsóide Horizontal",
    "Globular",
    "Hiperboloide",
    "Lenticular",
    "Ovoide",
    "Ovoide Invertido",
    "Piriforme",
    "Quadrangular",
    "Subglobular",
    "Tronco-Cônico",
)

PERFIS_GEOMETRICOS = (
    "Reto",
    "Côncavo",
    "Convexo",
    "Carenado Simples",
    "Carenado Duplo",
    "Sigmoide",
    "Composto",
)

PERFIS_TRECHO = (
    "Reto",
    "Côncavo",
    "Convexo",
    "Carenado Simples",
    "Sigmoide",
)

TIPOS_BASE = (
    "Reta",
    "Côncava",
    "Convexa",
)

CONTORNOS_PLANTA = (
    "Circular",
    "Oval",
    "Quadrangular",
    "Assimétrico",
)

# Litros. Intervalos [mínimo, máximo). Fora da tabela: faixas extra.
FAIXAS_VOLUME_L = (
    ("Pequeno", 0.150, 1.0),
    ("Médio", 1.0, 4.0),
    ("Grande", 4.0, 16.0),
    ("Extra grande", 16.0, 50.0),
)

UNIDADE_MEDIDA = "cm"
