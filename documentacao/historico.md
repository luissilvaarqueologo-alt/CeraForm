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

# Histórico do CeraForm

A gênese deste aplicativo remonta ao início da década de 1990, a partir das pesquisas teóricas e metodológicas da professora Cláudia Alves de Oliveira, arqueóloga da Universidade Federal de Pernambuco (UFPE). Em setembro de 1993, durante a VII Reunião Científica da Sociedade de Arqueologia Brasileira (SAB) em João Pessoa, Oliveira apresentou a proposta de um programa informático para o estudo de classificação e descrição da cerâmica pré-histórica baseado no sistema de classificação morfológica, a partir de parâmetros geométricos e matemáticos propostos por Anna O. Shepard (1957), Beatriz Tejero e Jaime Litvak (1968), e Jonathon Ericson e Edwin Stickel (1973).

Nos anos seguintes, contando com o suporte técnico do professor Davi Ferraz, do departamento de Engenharia Mecânica (UFPE), foi possível digitalizar os desenhos para reconstituir as formas e calcular o volume, permitindo a classificação relacionada ao tamanho da vasilha. No conjunto foram selecionadas seis vasilhas com formas e tamanhos diferentes para testar, o cálculo do volume através do computador. Os desenhos das peças foram digitalizados e transferidos para Programa AutoCad, onde foram realizados os cálculos de volume. O nosso interesse era desenvolver um programa onde pudéssemos reconstituir, com segurança, as vasilhas fragmentadas encontradas nos sítios pré-históricos. Através dos desenhos no computador podemos definir o centro de gravidade da peça, calcular o volume, reduzir ou ampliar para reprodução gráfica as vasilhas, classificar, quanto a forma geométrica e formar um banco de dados das formas cerâmicas dos grupos pré-históricos. Os ensaios e a metodologia foram documentados em 1998 na revista científica Clio Arqueológica nº 13, P. 157-171 no artigo "As Ceramistas de Conceição das Creoulas: Remanescentes de uma História" de autoria de Cláudia Alves de Oliveira, com a reconstituição gráfica e o cálculo volumétrico de vasilhas de Salgueiro (PE), como também na tese da mesma autora, Estilos tecnológicos da cerâmica pré-histórica no sudeste do Piauí – Brasil., em 2000, na Universidade de São Paulo- USP.

Para a classificação das formas das vasilhas relacionadas aos sólidos geométricos foi elaborado o programa VASOS.EXE, desenvolvido em Borland Pascal 7 para MS-DOS por Sandro Alves de Souza, egresso de Ciência da Computação e então programador pleno na UFPE (atuante no desenvolvimento de software de controle e processamento de imagens para tomografia computadorizada no Departamento de Física). O VASOS.EXE, em sua primeira versão, somente classificava os objetos em nove formas geométricas previamente definidas. Com a obsolescência das plataformas DOS, o aplicativo tornou-se inacessível e permaneceu inoperante por vários anos. Além do bloqueio de compatibilidade nos sistemas operacionais modernos, a formulação original (baseada na aproximação por arcos circulares rígidos) impunha restrições analíticas, gerando artefatos numéricos e imprecisões no desenho de pontos de inflexão, o VASOS2.EXE que seria a evolução do aplicativo desenhando a forma geométrica e calculando seu volume nunca chegou a ser completamente desenvolvido.

Passados 33 anos daquela apresentação na VII SAB o projeto foi retomado no segundo semestre de 2026 quando, convidada para proferir a aula magna e ministrar um minicurso de três dias sobre cerâmica arqueológica na UNIVASF, Oliveira relatou a existência do aplicativo e a impossibilidade de executar o software legado.

No curso estava o mestrando Luis Antonio Da Silva, pesquisador de gestão informatizada de acervos arqueológicos. Respaldado por uma carreira de mais de 30 anos em desenvolvimento de software e arquitetura de dados (com passagens por empresas como Telesp Celular, TIM, Almaviva e BBTS), Silva analisou o funcionamento do programa antigo com o viés de atualizá-lo para que pudesse funcionar em windows. Após a análise do software legado e ciente de suas limitações ele propôs a reformulação integral da ferramenta.

Sob a coautoria e orientação de Oliveira, e mantendo o aplicativo de 1994 apenas como matriz conceitual, Silva concebeu e programou o CeraForm. Os antigos arcos circulares foram substituídos por interpolação cúbica monótona (algoritmo PCHIP de Fritsch–Carlson) e polinômios de Hermite, eliminando oscilações espúrias e conferindo fidelidade milimétrica às descontinuidades reais das peças. Escrito em Python 3.11+, o software integra NumPy para operações vetoriais, banco de dados SQLite para persistência dos dados morfométricos e bibliotecas como Matplotlib, PyVista e Plotly para renderização volumétrica e reconstituição interativa em 2D e 3D.

Disponibilizado para pesquisa e preservação patrimonial sob termos de uso acadêmico, o CeraForm tem cronograma de expansão traçado. A meta dos pesquisadores é implementar módulos de visão computacional e geometria analítica para a reconstituição tridimensional automatizada de vasilhas completas a partir de fragmentos de bordas escaneados em 3D de alta resolução.
