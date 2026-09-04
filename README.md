<!--
=======================================================================
MÓDULO DE RECONSTITUIÇÃO GEOMÉTRICA DE CERÂMICAS - CERAFORM
=======================================================================
Autora (Idealização e Metodologia Arqueológica): Profa. Dra. Cláudia Alves de Oliveira
Autor (Arquitetura e Desenvolvimento de Software): Luís Antônio da Silva
Ano de Desenvolvimento: 2026
Linguagem e Tecnologias: Python 3.11+ | NumPy | SQLite | Matplotlib | PyVista / Plotly
Descrição Técnica:
O CeraForm é um sistema computacional para modelagem morfológica, cálculo volumétrico e reconstituição 2D/3D de cerâmicas arqueológicas. Substitui a aproximação por arcos circulares legados por uma nova formulação matemática baseada em interpolação cúbica monótona (PCHIP de Fritsch–Carlson) e polinômios de Hermite, garantindo continuidade suave, ausência de oscilações espúrias e precisão nas descontinuidades reais (carenas).
=======================================================================
Licença e Termos de Uso
CeraForm é disponibilizado gratuitamente para fins exclusivos de ensino, pesquisa e uso acadêmico não comercial.
É expressamente vedado qualquer uso comercial, direto ou indireto, sem prévia autorização por escrito dos autores.
Citação Obrigatória: Todo trabalho, publicação, relatório ou artigo derivado do uso deste software deve citar obrigatoriamente a fonte e seus autores.
© 2026 Cláudia Alves de Oliveira & Luís Antônio da Silva. Todos os direitos reservados.
=======================================================================
-->

# CeraForm

**CeraForm** é um sistema computacional para reconstituição geométrica de cerâmicas arqueológicas: modelagem morfológica, cálculo do volume da cavidade e visualização 2D/3D a partir de cotas internas medidas em centímetro.

O usuário informa as medidas do objeto reconstituído. O programa monta o meridiano da parede, **sugere** uma forma do catálogo de 19 classes, calcula volume e faixa de tamanho, mostra o corte 2D e o sólido 3D, e grava o registro em SQLite. A forma final é assinada pelos dois: o algoritmo sugere; o usuário confirma ou corrige.

Esta versão reconstitui o perfil com **interpolação cúbica monótona** (PCHIP de Fritsch–Carlson) e **polinômios de Hermite**, e não com arcos circulares.

Versão **1.0.0**. Licença acadêmica não comercial (`license.txt`).

## Download (Windows)

Para **usar** o CeraForm, baixe só o executável:

**[CeraForm_Windows.zip](https://github.com/luissilvaarqueologo-alt/CeraForm/releases/download/v1.0.0/CeraForm_Windows.zip)** — na [Release v1.0.0](https://github.com/luissilvaarqueologo-alt/CeraForm/releases/tag/v1.0.0).

Descompacte a pasta e execute `CeraForm.exe`. Não é preciso instalar Python.

## Registro no INPI

O depósito de programa de computador no INPI usa o **código-fonte** (hash do zip `CeraForm_fonte_INPI.zip`), não o instalador Windows. A pasta e o zip do INPI ficam fora deste repositório; o conteúdo depositado corresponde à versão 1.0.0 aqui etiquetada.

O pedido é feito em nome das **pessoas físicas** autoras, com **50%** de titularidade para cada uma, sem cessionário institucional (pessoa jurídica).

O número do registro, quando publicado pelo INPI, deve ser anotado neste README.

## Citação acadêmica

Todo trabalho que utilize resultados gerados pelo CeraForm deve citar o programa e os autores. O GitHub lê o arquivo `CITATION.cff` na raiz.

OLIVEIRA, Cláudia Alves de; SILVA, Luís Antônio da. CERAFORM: sistema computacional para reconstituição geométrica, modelagem morfológica e cálculo volumétrico de cerâmicas arqueológicas. Versão 1.0. Recife: [s. n.], 2026. Programa de computador. Python 3.11+, NumPy, SQLite, Matplotlib, PyVista/Plotly.


## Autoria

Titulares **pessoas físicas**, autoria em partes iguais (**50%** cada). O programa não é registrado em nome de pessoa jurídica.

- **Cláudia Alves de Oliveira** — idealização e metodologia arqueológica  
  ORCID: [https://orcid.org/0000-0002-3587-327X](https://orcid.org/0000-0002-3587-327X)  
  Currículo Lattes: [http://lattes.cnpq.br/7567746765435723](http://lattes.cnpq.br/7567746765435723)  
  E-mail: claudia.oliveira@ufpe.br

- **Luís Antônio da Silva** — arquitetura e desenvolvimento de software  
  ORCID: [https://orcid.org/0009-0006-9660-9735](https://orcid.org/0009-0006-9660-9735)  
  Currículo Lattes: [http://lattes.cnpq.br/0945424503706599](http://lattes.cnpq.br/0945424503706599)  
  E-mail: luis.silva.arqueologo@gmail.com

## Licença

Uso gratuito para pesquisa, ensino e atividades acadêmicas sem fins lucrativos. Uso comercial é vedado sem autorização prévia dos autores. Texto completo: `license.txt`.
