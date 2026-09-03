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

Documento de referência técnica e científica do aplicativo CeraForm de reconstituição geométrica de cerâmicas (agosto de 2026). Destina-se a quem for conferir o programa: descreve o fluxo de trabalho, as fórmulas aplicadas no código, a árvore de decisão da inferência de forma e o relatório das suítes unitárias que passaram.

O sistema anterior (VASOS.EXE, 1994) reconstituía o perfil com arcos circulares e segmentos retos a partir de quatro medições e oito classes geométricas. Este aplicativo inspira-se nesse olhar para desenvolver um algoritmo completamente novo. Entre os pontos medidos a parede é interpolada por um spline cúbico monótono (PCHIP de Fritsch–Carlson) ou por segmentos retos. A forma sai de razões adimensionais sobre o catálogo de 19 classes geométricas.

O volume da cavidade tem formulação analítica por dois segmentos de revolução, além da integral trapezoidal na malha fina. O objetivo é um resultado equivalente ao desenho original no papel milimetrado, que possa ser extrapolado para uma representação tridimensional do objeto, com o cálculo do seu centro de equilíbrio e sua capacidade volumétrica.

Para compreender o impacto dessa mudança, basta imaginar o desafio de vetorizar o perfil de um vaso a partir de um conjunto discreto de pontos medidos ao longo de sua superfície. Antigamente, ao tentar unir esses pontos por meio de múltiplos arcos de círculo, o processo frequentemente resultava em transições angulosas ou na criação de ondulações e "barrigas" artificiais que não existiam no artefato original. O novo método supera essa limitação ao calcular uma curva matemática que se ajusta com precisão ao comportamento real da peça.

A propriedade de monotonicidade do algoritmo PCHIP assegura que a linha siga estritamente a tendência dos dados originais, impedindo o surgimento de oscilações espúrias. Isso significa que, se a parede do vaso apresenta uma inclinação ascendente contínua, a reconstrução gráfica não criará falsas reentrâncias ou saliências. Paralelamente, os polinômios de Hermite garantem que a curva passe exatamente por cada coordenada informada, preservando a suavidade nas áreas de transição gradual e mantendo a nitidez necessária para registrar as descontinuidades morfológicas reais do objeto, como carenas, gargalos e lábios.

Como resultado direto dessa reformulação, o vetor gerado reflete a anatomia genuína do artefato cerâmico. A eliminação das distorções no contorno assegura uma melhoria substancial na exatidão das métricas derivadas, conferindo alta precisão arqueométrica ao cálculo do volume interno e à geração do modelo tridimensional.

Para conferir se a sugestão de forma está correta, há duas coisas a verificar: os números de corte da seção 12 (por exemplo 0,28 para discoide) têm que ser os mesmos do código; e o sucesso nos testes da seção 18.

---

## 1. O que o sistema faz, em uma frase

O usuário informa as **cotas internas** de um objeto reconstituído. O programa:

1. monta o **meridiano** analítico (corte da parede no plano vertical \(Z\times R\));
2. **sugere** uma forma do catálogo de 19 nomes, pela árvore de razões adimensionais (`classificarForma`);
3. calcula o **volume da cavidade** (analítico por zonas e, na ficha, integral trapezoidal da malha) e a **faixa de tamanho**;
4. calcula o **centro de massa** da casca e um comentário de estabilidade da base;
5. mostra o corte **2D** (pré-visualização na tela e exportações) e o sólido **3D** oco;
6. grava o registro em SQLite, com a forma **confirmada** (o usuário pode corrigir a sugestão).

A forma final é assinada pelos dois: o algoritmo sugere; o usuário confirma ou corrige. Não há histórico de correção — vale o valor atual.

---

## 2. O que esta versão não faz

Estas exclusões estão fechadas no aplicativo:

- não cadastra **fragmento** como objeto (o registro é sempre o objeto reconstituído);
- não trata **apêndices** (bico, alça);
- não classifica boca, borda, lábio nem tratamento de superfície;
- não importa o arquivo histórico VASOS.ARQ;
- não guarda proveniência, tradição, contexto, fotografia nem bibliografia;
- unidade única: **centímetro**; diâmetros **internos**;
- sem tolerância de erro de medição (o número digitado é o que vale).

Start do Aplicativo:

```bash
python3 run_desktop.py
```

---

## 3. Identificador e gravação

Cada objeto é identificado por:

- **nome do sítio** por extenso (obrigatório);
- **número do desenho** (obrigatório): no máximo 20 caracteres; algarismos, letras, ponto, hífen e barra.

O par (nome do sítio, número do desenho) é único no banco. Se o usuário mudar um desses dois campos num registro já gravado, o programa cria um registro novo em vez de sobrescrever o antigo.

Para gravar, o núcleo mínimo de medidas é:

| Campo na tela | Significado |
| --- | --- |
| Altura total | da base até a borda, em centímetro (> 0) |
| Diâmetro da borda | diâmetro interno na boca (> 0) |
| Maior diâmetro da peça | maior diâmetro interno do perfil (> 0) |
| Altura da base até o maior diâmetro | altura em que ocorre o maior diâmetro (≥ 0 e ≤ altura total) |
| Diâmetro da base | diâmetro interno da base (≥ 0; **0 cm** é válido c/ base convexa) |
| Tipo de base (obrigatório) | Reta, Côncava ou Convexa — reconstitui o fundo |
| Perfil geométrico (obrigatório) | Reto, Côncavo, Convexo, Carenado Simples, Carenado Duplo, Sigmoide ou Composto |

Num cadastro **novo** (tela limpa), as listas (tipo de base, perfil geométrico, contorno da vista de cima, trechos do composto, forma confirmada) começam **em branco**, como os campos numéricos. Não se preenche valor por padrão: o usuário escolhe. Se o perfil geométrico for **Composto**, também são obrigatórios o perfil do trecho junto à base e o perfil do trecho junto à borda.

O **tipo de base** completa a reconstituição do fundo (seção 8). O **perfil geométrico** define como a parede é interpolada (seção 6). A reconstituição na tela só avança quando tipo de base e perfil geométrico estão escolhidos (além das medidas do núcleo).

---

## 4. Sistema de coordenadas

Imagine o vaso em pé sobre a mesa.

- O eixo **Z** é vertical. **Z = 0** na base da parede (depois, se a base for côncava ou convexa, o apoio da mesa pode ficar um pouco abaixo).
- O **raio** \(R\) é a metade do diâmetro interno: o programa **nunca** interpola diâmetro misturado com raio.

\[
R = \frac{D}{2}\quad\text{(se \(D = 0\), o raio na base é 0)}.
\]

Um piso numérico mínimo só entra onde a divisão por zero quebraria a malha; não é cota arqueológica. Diâmetro da base **0 cm** é medição válida (tigela/taça que fecha no eixo).

O meridiano é a curva \((Z, R)\) no plano do corte. O sólido 3D nasce **girando** essa curva em torno do eixo Z (revolução), com ajuste se a planta não for circular (seção 11).

---

## 5. Os pontos de controle (estações)

Antes de desenhar a parede, o programa junta todas as cotas num conjunto de estações \((Z_i, R_i)\):

| Altura \(Z\) | Raio \(R\) |
| --- | --- |
| \(0\) | metade do diâmetro da base |
| altura da base até o maior diâmetro | metade do maior diâmetro da peça |
| altura total | metade do diâmetro da borda |
| metade da altura total (se houver diâmetro da cintura) | metade do diâmetro da cintura |
| \(1/4\), \(1/2\) e \(3/4\) da altura total (se preenchidos) | metade do diâmetro correspondente |
| altura da carena / da segunda quebra (se preenchidas) | metade do diâmetro da quebra |
| altura da junção bojo–pescoço (se preenchida) | metade do diâmetro da junção |

Regras de limpeza:

- as estações são ordenadas por \(Z\) crescente;
- se duas cotas caem na mesma altura, fica o **maior** raio;
- medições extras só entram se \(0 < Z <\) altura total e o diâmetro for positivo.

Os três diâmetros a um quarto, à metade e a três quartos da altura total são **opcionais em qualquer peça** (com ou sem anel na base). Vazios, o perfil usa só o núcleo; preenchidos, a parede passa por esses pontos. Na tela o grupo chama-se **Medições extras**, com os campos **1/4 da altura (cm)**, **1/2 da altura (cm)** e **3/4 da altura (cm)** (as alturas o programa calcula a partir da altura total).

A **altura da junção bojo–pescoço** e o **diâmetro da junção bojo–pescoço** também entram em qualquer perfil (não só Composto). A altura da junção tem de ser distinta da altura do maior diâmetro (tolerância \(0{,}05\,\mathrm{cm}\)) e ficar estritamente entre a base e a borda — em geral entre a barriga e a boca.

\[
Z_{1/4} = \tfrac{1}{4}\,H,\qquad
Z_{1/2} = \tfrac{1}{2}\,H,\qquad
Z_{3/4} = \tfrac{3}{4}\,H
\]

O **diâmetro da cintura** é outro campo: não precisa coincidir com a meia altura.

---

## 6. Perfil geométrico — o que cada valor faz na parede

Campo na tela: **Perfil geométrico (obrigatório)**. Valores:

Reto; Côncavo; Convexo; Carenado Simples; Carenado Duplo; Sigmoide; Composto.

Não se usa a nomenclatura antiga do VASOS2.EXE (interna / linear / externa) na tela. Se um dado legado ainda trouxer essa palavra, o mapa interno é só este:

- externa → Convexo
- linear → Reto
- interna → Côncavo

### 6.1 Segmentos retos (sem suavizar cantos)

Usados quando o perfil é **Reto**, **Carenado Simples** ou **Carenado Duplo**.

Entre duas estações consecutivas, o raio cresce (ou decresce) em linha reta:

\[
R(Z) = R_i + (R_{i+1}-R_i)\,\frac{Z-Z_i}{Z_{i+1}-Z_i}
\]

Isso preserva a **quebra** (carena): o canto não é arredondado.

### 6.2 Parede curva (PCHIP + Hermite)

Usados quando o perfil é **Convexo**, **Côncavo** ou **Sigmoide** (e nos trechos curvos do composto).

A interpolação é em dois passos:

1. calcular a derivada \(dR/dZ\) em cada estação pela regra **PCHIP** (Fritsch–Carlson), que não oscila e não cria “barriga extra” entre os pontos medidos;
2. interpolar com o **polinômio cúbico de Hermite** em cada intervalo.

Se o SciPy estiver instalado, usa-se `PchipInterpolator` e depois `CubicHermiteSpline`. Caso contrário, o próprio NumPy reproduz a mesma regra, descrita a seguir.

#### Derivadas interiores (Fritsch–Carlson)

Sejam os passos e as inclinações secantes

\[
h_i = Z_{i+1}-Z_i,\qquad
\delta_i = \frac{R_{i+1}-R_i}{h_i}.
\]

No vértice interior \(i\):

- se \(\delta_{i-1}\cdot\delta_i \le 0\) (a parede muda de subir para descer, ou o contrário), então \(d_i = 0\) — o extremo local fica **no ponto medido**, sem vale antes nem depois;
- senão

\[
w_1 = 2h_i + h_{i-1},\qquad
w_2 = h_i + 2h_{i-1},\qquad
d_i = \frac{w_1+w_2}{\dfrac{w_1}{\delta_{i-1}}+\dfrac{w_2}{\delta_i}}.
\]

#### Derivadas nos extremos

No primeiro ponto (e o simétrico no último):

\[
s = \frac{(2h_0+h_1)\,\delta_0 - h_0\,\delta_1}{h_0+h_1}.
\]

- se \(s\cdot\delta_0 \le 0\), então \(d_0 = 0\);
- se \(\delta_0\cdot\delta_1 < 0\) e \(|s| > 3|\delta_0|\), então \(d_0 = 3\delta_0\);
- senão \(d_0 = s\).

#### Junta suave no maior diâmetro

Depois de obter as derivadas, o programa **anula** \(dR/dZ\) na estação do maior diâmetro da peça (quando ela não é a base nem a borda). Assim a barriga não “passa do ponto” e os dois lados encontram-se com tangente horizontal.

#### Polinômio de Hermite em cada intervalo

Com \(t = (Z-Z_i)/h_i\), \(0\le t\le 1\):

\[
\begin{align*}
H_{00}(t) &= 2t^3-3t^2+1,\\
H_{10}(t) &= t^3-2t^2+t,\\
H_{01}(t) &= -2t^3+3t^2,\\
H_{11}(t) &= t^3-t^2,
\end{align*}
\]

\[
R(Z) = H_{00}\,R_i + H_{10}\,h_i\,d_i + H_{01}\,R_{i+1} + H_{11}\,h_i\,d_{i+1}.
\]

O raio interpolado nunca desce abaixo de \(0{,}002\,\mathrm{cm}\).

### 6.3 Por que não dois arcos circulares independentes

Dois arcos que se encontram no maior diâmetro podem ter a mesma tangente (continuidade \(C^1\)) e mesmo assim saltar de curvatura (descontinuidade \(C^2\)). Isso lia-se como acinturamento no corte e como degrau no 3D. O PCHIP evita a oscilação típica de interpoladores de grau alto (fenômeno de Runge) e respeita os máximos medidos.

### 6.4 Perfil composto (bojo + pescoço)

O composto cobre uma peça com **dois trechos**:

- trecho junto à base (bojo), até a **junção bojo–pescoço**;
- trecho junto à borda (pescoço), da junção até a borda.

Cada trecho tem o seu perfil (Reto, Côncavo, Convexo, Carenado Simples ou Sigmoide).

A altura da junta é a **altura da junção**. Se ela não for informada, o programa usa a altura do maior diâmetro:

\[
Z_{\mathrm{junta}} =
\begin{cases}
\text{altura da junção}, & \text{se } > 0,\\
\text{altura do maior diâmetro}, & \text{caso contrário.}
\end{cases}
\]

Abaixo de \(Z_{\mathrm{junta}}\) interpola-se com o perfil do bojo; acima, com o perfil do pescoço. **A junção bojo–pescoço é sempre arredondada** (\(dR/dZ = 0\) no estreito: parede vertical no pescoço, como no maior diâmetro). Não se desenha canto nem ângulo reto nesse ponto — um pescoço de cerâmica quase nunca o tem. Se a altura da junção está preenchida e os dois trechos do composto são curvos, entram num único PCHIP (a junta não parte a curva). Com perfil **Convexo** (sem ser Composto), a junção continua a ser estação de controlo: o meridiano passa por ela. Carena (quebra ≥ 18°) é outro campo, não a junta do pescoço.

### 6.5 Reforço do pescoço piriforme

Se a barriga está **baixa** e a borda é **estreita**, uma interpolação suave demais entre o maior diâmetro e a borda vira um ovo, não uma pera. Por isso, quando **não** se trata de Reto/Carenado, o programa pode inserir uma estação extra no pescoço:

Condições:

\[
\frac{\text{altura do maior diâmetro}}{\text{altura total}} < 0{,}40
\quad\text{e}\quad
\frac{\text{diâmetro da borda}}{\text{maior diâmetro}} < 0{,}55.
\]

Se ainda não houver nenhuma cota entre \(Z_{\mathrm{lo}}\) e \(Z_{\mathrm{hi}}\),

\[
Z_{\mathrm{lo}} = H_{\max} + 0{,}10\,(H-H_{\max}),\qquad
Z_{\mathrm{hi}} = 0{,}90\,H,
\]

insere-se

\[
Z_p = H_{\max} + 0{,}36\,(H-H_{\max}),\qquad
R_p = R_{\mathrm{borda}} + 0{,}18\,(R_{\max}-R_{\mathrm{borda}}).
\]

Isso aperta o pescoço sem inventar uma carena.

A malha fina do perfil usa 240 cotas em \(Z\), mais todas as estações de controle, para o maior diâmetro e as quebras caírem exatamente num ponto da curva.

---

## 7. Quebras do meridiano (carena visível)

Uma **carena** não é o nome do perfil: é uma mudança de direção grande o bastante no corte.

Em cada vértice interior das estações, tomam-se os vetores

\[
\vec{v}_1 = (Z_i-Z_{i-1},\; R_i-R_{i-1}),\qquad
\vec{v}_2 = (Z_{i+1}-Z_i,\; R_{i+1}-R_i).
\]

O ângulo entre eles (em graus) é

\[
\theta = \arccos\!\left(
  \mathrm{clip}\!\left(
    \frac{\vec{v}_1\cdot\vec{v}_2}{|\vec{v}_1|\,|\vec{v}_2|},\;
    -1,\; 1
  \right)
\right).
\]

Há quebra se \(\theta \ge 18^\circ\).

Para a **classificação**, o programa usa o meridiano interpolado (não só as três estações do núcleo):

- existe quebra visível (\(\theta \ge 18^\circ\))? então a forma lisa (Piriforme, Ovóide, elipsóide) **não** se aplica;
- existe quebra junto do maior diâmetro? (tolerância \(\max(0{,}08\,H,\; 0{,}2\,\mathrm{cm})\))
- existe **outra** quebra fora dessa vizinhança **e** fora da junta do perfil composto?

A segunda resposta afirma **Carenado Duplo**. Uma quebra só afirma **Carenado**. A junta do composto não vira carena dupla só porque o bojo muda de perfil no pescoço.

---

## 8. Tipo de base

A parede começa no anel da base (ou no eixo, se o diâmetro da base for 0 cm). O fundo, do centro até esse anel, depende do **tipo de base** (campo obrigatório na tela).

### 8.1 Base com anel (\(D_{\mathrm{base}} > 0\))

Seja \(R_b\) o raio interno na base e \(s = 0{,}20\,R_b\) a sagita (flecha) do fundo. Com \(r\) indo de \(0\) até \(R_b\):

| Tipo de base | Equação do fundo \(z(r)\) | Onde apoia |
| --- | --- | --- |
| Reta | \(z = 0\) | disco plano |
| Côncava | \(z = s\bigl(1-(r/R_b)^2\bigr)\) | anel da base (fundo reentrante) |
| Convexa | \(z = s\,(r/R_b)^2\) | centro (calota para fora) |

Depois o meridiano da parede é deslocado para cima pela altura do fundo no **anel** (\(z\) em \(r = R_b\)), para **Z = 0** ficar no apoio da mesa. Na base convexa isso vale \(+s\) (o anel fica à sagita; o contato continua no centro, \(r = 0\), \(Z = 0\)). Na côncava o anel já está em \(Z = 0\) e a parede não sobe. A calota do fundo **não** recebe essa translação extra: as suas cotas já estão no mesmo referencial da mesa.

Na base convexa, o raio de curvatura no centro da parábola \(z = (s/R_b^2)\,r^2\) é

\[
\rho = \frac{R_b^2}{2s} = \frac{R_b}{0{,}40} = 2{,}5\,R_b.
\]

Esse \(\rho\) entra só no comentário de equilíbrio (seção 13), não na forma catalogada.

### 8.2 Diâmetro da base 0 cm (fundo arredondado)

Quando o diâmetro da base é **0 cm** (tipo de base **Convexa**, sem anel) e a parede **não** é reta/carenada, o fundo é arredondado: um **círculo** ou uma **elipse** da borda à borda, com tangente horizontal no eixo (apoio em calota — **sem pontinha**).

Dois casos, segundo as medidas do núcleo:

- **Maior diâmetro na borda** (\(H_{\max}\) junto da boca): uma só curva — arco circular se \(H \le R = D_b/2\); semi-elipse de eixos \(R\) e \(H\) se a peça é mais profunda que larga.
- **Barriga abaixo da borda** (mesmo que \(D_{\max}\) e \(D_b\) diferam pouco, como 23{,}5 cm vs 21 cm): duas elipses (círculo quando os semi-eixos coincidem) que se encontram no maior diâmetro, com parede vertical nesse plano:

  - inferior: polo no fundo \((r=0,\,z=0)\), equador em \(Z = H_{\max}\), \(R = D_{\max}/2\);
  - superior: do equador até a borda \(D_b\) em \(Z = H\).

Assim a silhueta **passa** pelo maior diâmetro na altura informada e pela borda; as cotas coincidem com o desenho.

Se houver cotas extras (1/4, 1/2 ou 3/4 da altura total, junção bojo–pescoço, amostra, carena), elas **entram no meridiano** mesmo com diâmetro da base 0 cm — inclusive quando o maior diâmetro está perto da borda (ovoide invertido / tigela). Uma cota conta se a altura está estritamente entre base e borda e **difere** da altura do maior diâmetro por mais de \(0{,}05\,\mathrm{cm}\) (meio milímetro). Se a junção for gravada na **mesma** altura que o maior diâmetro, não há pescoço: é a cota da barriga.

- cota **abaixo** da barriga: calota circular até o primeiro ponto medido (tangente horizontal no eixo), depois PCHIP pelas demais estações;
- cota **acima** da barriga: elipse até o maior diâmetro, depois PCHIP pelo pescoço até a borda.

Sem nenhuma dessas cotas extras, vale a elipse/círculo do núcleo (regra antiga).

Parede **reta** ou **carenada** com diâmetro da base 0 cm continua a fechar em ponta (cone / bicone). Não se acrescenta calota parabólica à parte. No 3D, o interior **não** ganha disco plano a meia altura (`fundo_plano=False`).

---

## 9. Volume da cavidade

O volume é o da **cavidade interna** (o que o vaso conteria). As medidas entram em centímetro. Há dois cálculos complementares no módulo `ceraform/volume.py`.

### 9.1 Integração analítica por dois segmentos (`calcular_volume`)

O sólido de revolução é seccionado no plano \(Z = H_{\max}\) (altura do maior diâmetro):

- segmento inferior, altura \(h_{\mathrm{inf}} = H_{\max}\), raios \(a = D_{\mathrm{base}}/2\) e \(b = D_{\max}/2\);
- segmento superior, altura \(h_{\mathrm{sup}} = H - H_{\max}\), raios \(a = D_{\max}/2\) e \(b = D_b/2\).

Segmento de altura nula não entra na soma. Com espessura da parede \(t > 0\), as cotas passam a ser as internas **antes** da integração:

\[
H' = \max(H-t,\,0),\quad
D' = \max(D-2t,\,0)\ \text{em } D_{\max}, D_b, D_{\mathrm{base}},\quad
H_{\max}' = \mathrm{clip}(H_{\max}-t,\,0,\,H').
\]

#### Perfil retilíneo (tronco de cone)

\[
V_{\mathrm{tronco}} = \frac{\pi h}{3}\,(a^2 + ab + b^2)
= \frac{\pi h}{12}\,(D_1^2 + D_1 D_2 + D_2^2).
\]

(As duas escritas são idênticas: \(D = 2a\).) Cilindro: \(a = b\) recupera \(\pi a^2 h\). Cone: \(a = 0\) recupera \(\pi b^2 h / 3\).

#### Perfil convexo (zona esférica)

\[
V_{\mathrm{zona}} = \frac{\pi h}{6}\,(3a^2 + 3b^2 + h^2).
\]

Dois hemisférios (\(H = D_{\max}\), \(H_{\max} = H/2\), \(D_b = D_{\mathrm{base}} = 0\)) recuperam o volume da esfera \(\frac{4}{3}\pi R^3\).

#### Perfil côncavo ou composto

\[
V_{\mathrm{côncavo}} = \frac{\pi h}{6}\,(3a^2 + 3b^2 - h^2),
\]

limitado ao intervalo \([0,\, V_{\mathrm{tronco}}]\) para a zona reentrante não ultrapassar o tronco linear nem ficar negativa.

#### Conversão de unidades

\[
V_{\mathrm{mL}} = V_{\mathrm{cm}^3},\qquad
V_{\mathrm{L}} = \frac{V_{\mathrm{cm}^3}}{1\,000}.
\]

(\(1\,\mathrm{L} = 1\,000\,\mathrm{cm}^3\); \(1\,\mathrm{mL} = 1\,\mathrm{cm}^3\).)

### 9.2 Integral trapezoidal na malha fina (ficha 2D/3D)

Na tela, o volume de transbordamento usa o meridiano interpolado (240 passos em \(Z\)). Para planta circular, oval ou assimétrica:

\[
A(Z) = \pi\,\bigl(R(Z)\,s_x\bigr)\,\bigl(R(Z)\,s_y\bigr).
\]

(Na planta circular, \(s_x = s_y = 1\), e recupera-se \(A = \pi [R(Z)]^2\).)

Para planta **quadrangular**, a seção é um retângulo de semi-lados \(s_x R(Z)\) e \(s_y R(Z)\):

\[
A(Z) = 4\,s_x\,s_y\,\bigl[R(Z)\bigr]^2,
\]

e **não** a da elipse circunscrita.

\[
V_{\mathrm{cm}^3} = \int_{Z_{\min}}^{Z_{\max}} A(Z)\,dZ
\approx
\sum_i \frac{A_i+A_{i+1}}{2}\,(Z_{i+1}-Z_i).
\]

Além do volume de **transbordamento** (100 % da altura total), o programa calcula a **capacidade efetiva de uso** até 85 % e até 90 % da altura total, cortando o mesmo perfil nessas cotas e integrando de novo. A faixa de tamanho (seção 10) continua a usar o volume a 100 %.

As cotas \(Z_{\mathrm{corte}} = 0{,}85\,H\) e \(0{,}90\,H\) podem cair **entre** dois nós. O programa interpola o raio exato \(R(Z_{\mathrm{corte}})\) e **inclui esse ponto como limite superior** da regra do trapézio. Sem isso, o último intervalo ficaria truncado no nó imediatamente abaixo do corte.

---

## 10. Faixas de tamanho

O tamanho do objeto segue o volume da cavidade. Os intervalos da tabela são semiabertos \([a, b)\), com dois recortes nas pontas:

| Tamanho | Volume \(V\) (litro) | Observação na ficha |
| --- | --- | --- |
| Pequeno | \(V < 0{,}150\) | “abaixo de 0,150 L” |
| Pequeno | \(0{,}150 \le V < 1{,}0\) | — |
| Médio | \(1{,}0 \le V < 4{,}0\) | — |
| Grande | \(4{,}0 \le V < 16{,}0\) | — |
| Extra grande | \(16{,}0 \le V < 50{,}0\) | — |
| Extra grande | \(V \ge 50{,}0\) | “a partir de 50,0 L” |

Conforme sugerido pela Dra. Cláudia, Pequeno vai até 1,0 L (incluindo o que estiver abaixo de 0,150 L, com observação); Extra grande começa em 16,0 L (incluindo o que estiver a partir de 50,0 L, com observação).

---

## 11. Planta (vista de cima) e sólido 3D

### 11.1 Escalas da planta

O meridiano é sempre calculado no plano do **maior diâmetro da peça**. Se a planta não for circular **e** houver comprimento e largura da planta (vista de cima), o sólido é esticado:

\[
s_x = \frac{\text{comprimento da planta}/2}{\text{maior diâmetro}/2},\qquad
s_y = \frac{\text{largura da planta}/2}{\text{maior diâmetro}/2}.
\]

No 3D usa-se a razão \(s_y/s_x\), porque o meridiano já levou \(s_x\) no eixo X.

Se a planta for circular, ou se faltar comprimento/largura: \(s_x = s_y = 1\).

### 11.2 Seção horizontal

Com ângulo \(\theta\) em torno do eixo:

**Circular ou oval** (elipse):

\[
x = R\cos\theta,\qquad y = R\,s_y\sin\theta.
\]

**Quadrangular** (retângulo de semi-eixos \(A = R\) e \(B = R\,s_y\)):

\[
\rho(\theta) = \min\left(
  \frac{A}{\max(|\cos\theta|,\,10^{-9})},\;
  \frac{B}{\max(|\sin\theta|,\,10^{-9})}
\right),
\qquad
x = \rho\cos\theta,\quad y = \rho\sin\theta.
\]

Essa é a equação polar de um retângulo alinhado aos eixos: a parede “bate” no lado vertical ou no horizontal, o que ocorrer primeiro. Assim um objeto marcado Quadrangular não sai oval no 3D.

**Assimétrico** usa a mesma elipse da oval (o aplicativo não deforma o perímetro além das duas escalas).

### 11.3 Peça oca

O 3D não é um sólido maciço. A polilinha da argila percorre:

fundo externo → parede externa → lábio (borda) → parede interna → fundo interno.

A espessura da parede, se o campo estiver vazio ou abaixo de \(0{,}002\,\mathrm{cm}\), vale **0,2 cm** só para o desenho 3D (não altera o volume da cavidade, que usa o perfil interno). O raio interno nunca desce abaixo de \(0{,}05\,\mathrm{cm}\). Com anel na base, o piso interno fica a uma profundidade igual à espessura, limitada a 35 % da altura da peça, para a boca permanecer aberta. Se o perfil fecha no eixo (diâmetro da base 0 cm com base convexa, seção 8.2), o interior segue o meridiano até o eixo — **sem** disco plano interior artificial.

A malha de revolução do 3D interpola o meridiano **já calculado** em linha reta ao longo de \(Z\) (`np.interp`). Não se reaplica PCHIP nessa etapa: reaplicar com derivada nula no bojo arredondava as carenas.

O corte 2D (seção 11.4) desenha a face externa por offset na normal; o 3D continua a casca radial \(r-t\). São dois desenhos da mesma espessura da parede, não a mesma polilinha.

### 11.4 Corte 2D (tela, PNG e PDF)

O corte (módulo `ceraform/visual_2d.py`, Matplotlib) mostra os dois lados do meridiano (espelhados), o fundo, o eixo e as cotas por extenso: diâmetro da borda, maior diâmetro da peça, diâmetro da base, altura da base até o maior diâmetro, altura total (e, se houver, a segunda quebra). Na ficha ao lado do desenho, as medições extras preenchidas aparecem como **1/4 da altura**, **1/2 da altura** e **3/4 da altura**. Cotas redundantes (valores iguais a outra já desenhada, ou diâmetro da base 0) são omitidas. Se houver **espessura da parede**, a face externa é o meridiano interno deslocado na perpendicular (fundo incluído), desenhado num único tracejado que fecha no eixo quando o diâmetro da base é 0 cm; o lábio (fechamento na borda) é **horizontal**, na mesma altura da borda interna. No flanco esquerdo a cota usa o rótulo **espes. parede**. A malha 3D fica em `ceraform/vista_solido.py`.

**Posição dos rótulos das cotas (corte técnico — tela e PDF):**

- diâmetro da borda — acima da linha da cota;
- maior diâmetro da peça e diâmetro da base — abaixo da linha da cota;
- altura total — na extremidade superior da linha vertical, acima dela;
- altura da base até o maior diâmetro — na extremidade inferior da linha vertical, abaixo dela; o nome parte em duas linhas (`altura da base até` / `o maior diâmetro`) e o valor na terceira;
- altura da segunda quebra (se existir) — a **meio** da linha vertical, para não sobrepor as outras duas cotas de altura.

No PDF técnico os trilhos verticais ficam compactos à direita da peça. Há **dois modos** de apresentação do perfil:

| Modo | Uso | Fundo | Escala gráfica |
| --- | --- | --- | --- |
| **Corte técnico** (tela / PNG) | pré-visualização com cotas | branco, sem milimetrado | **não** |
| **Publicação** (tela / PNG) | elevação com elipse da borda, para figura de documento | branco, sem milimetrado | **sim** — ver abaixo |
| **PDF** (corte técnico) | folha A4 para arquivo/impressão | milimetrado (1 cm do papel = 1 cm na grade) | **sim** — barra zebra com marcas em cm do objeto (sem texto «ESCALA GRÁFICA» nem «1:n» na folha) |

O botão **PDF** da interface gera **sempre** o corte técnico via `desenhar_perfil_completo(..., modo="pdf")` + `preparar_folha_exportacao` (o modo Publicação exporta só PNG da tela; o botão PDF fica desativado nesse modo).

**Barra de escala na tela Publicação** (independente do PDF):

- canto inferior direito da **janela** (coordenadas da figura; não acompanha o vaso nem o encolhimento do eixo);
- **tamanho visual fixo** (mesma zebra em qualquer peça); só os números mudam, conforme a escala dos eixos na tela;
- marcas e valores acima da barra; o texto **cm** centrado **abaixo** da barra.

**Campo do desenho no PDF técnico** (único padrão):

- 2,5 cm das bordas esquerda, direita e inferior da folha;
- 1 cm abaixo do bloco do cabeçalho;
- a peça + cotas é centrada nesse retângulo; só a **escala** muda para caber (maior razão discreta \(a{:}b\) que ainda entra — ampliação 5:1…2:1, intermediárias como 5:6 ou 4:5, natural 1:1, redução 1:2…).

A barra de escala do **PDF** fica no canto inferior direito do milimetrado, a **0,5 cm** acima da borda inferior da grade. O comprimento no papel é escolhido para marcas redondas em cm do objeto. Cabeçalho (nome do sítio, número do desenho, forma, volume, tamanho) no alto da folha.

Na tela (corte técnico), o mesmo cabeçalho fica no alto da janela; o corte fica centrado, sem eixos numéricos nem grade.

### 11.5 Interação no sólido 3D

A vista 3D (`VistaSolido` em `ceraform/vista_solido.py`) usa PyVista em **modo off-screen**: a cada movimento a câmera é reposicionada e um *screenshot* é mostrado num `Text` do Tk (não é a janela interativa nativa do VTK).

- arrastar com o botão esquerdo: órbita (azimute e elevação; a elevação evita os polos exatos ±90° para não perder o giro horizontal);
- zoom: teclas **+** e **−**. No Linux a roda do mouse (e o gesto de pinça) também amplia e reduz. No Windows 11 a roda **não** chega ao retrato 3D (o sólido é um *screenshot* Tk, não a janela VTK); a dica na tela cita só as teclas. O redesenho do preview **não** zera o zoom;
- aparência de cerâmica: **PBR** (rugosidade 0,35), cor de argila (`#C47A52`) e luzes de estúdio. No Linux (código-fonte) entram também textura de ambiente (IBL) e anti-aliasing MSAA 8×. No Windows (executável ou Wine) o cubemap IBL e o MSAA 8× ficam de fora: em vários notebooks o OpenGL trava nesses dois passos, sem levantar exceção Python.

Se o PyVista não estiver disponível **no desenvolvimento** (código-fonte sem a biblioteca), o programa cai para uma superfície Matplotlib 3D. O executável Windows leva PyVista e VTK embarcados. Se o VTK falhar com exceção, o 3D cai para Matplotlib e o exe grava `ceraform_erro.txt` ao lado do programa. Se o OpenGL **travar** (a janela fica parada, sem arquivo de erro), o próximo arranque deixa o rastro das etapas em `ceraform_3d.txt` na mesma pasta — a última linha indica onde parou.

A pasta `.mplconfig` ao lado do exe é cache do Matplotlib; pode nascer vazia e não indica falha.

**PNG do 3D** (botão PNG nessa tela): monta a figura como na janela — painel «Dados do objeto» à esquerda e o sólido à direita (`_compor_png_3d_com_ficha` em `ceraform/ui_desktop.py`). A ficha usa **Times New Roman 12**, a mesma da interface (`ceraform/fonte.py`, `TAMANHO = 12`). Valores longos (nome do sítio) não são cortados: o painel alarga ou o texto quebra de linha. O PNG não é uma fotografia da janela; é a mesma composição, com essa tipografia.

---

## 12. Inferência da forma geométrica

Há 19 nomes fechados (catálogo em `ceraform/constantes.py`). O algoritmo **não** reconhece a peça por visão: aplica uma **árvore de decisão** sobre razões adimensionais (`classificarForma` em `ceraform/classificar.py`). Essa árvore é a fonte da **forma principal**. Uma heurística de pontuação da 1.ª versão (`_score_par`) permanece só para a **forma secundária** e para marcar aproximação. O usuário confirma ou troca o nome na tela ao gravar.

A integridade da inferência é a reprodução exata desta árvore (a **ordem dos testes importa**) e a passagem das 20 provas da seção 18.1. Os limiares não são “opinião”: são constantes do código, conferidas contra silhuetas analíticas (esfera, cilindro, cone, ovoides, disco).

### 12.1 Entradas e validade

Argumentos de `classificarForma(H, Dmax, Db, D0, hmax, perfil)`:

| Símbolo | Campo na tela |
| --- | --- |
| \(H\) | altura total |
| \(D_{\max}\) | maior diâmetro da peça |
| \(D_b\) | diâmetro da borda |
| \(D_0\) | diâmetro da base |
| \(h_{\max}\) | altura da base até o maior diâmetro |
| perfil | perfil geométrico (Reto, Côncavo, Convexo, …) |

Sinônimos aceitos do perfil: `Retilineo` / `linear` → Reto; `Concavo` / `interna` → Côncavo; `externa` → Convexo.

Medidas **inválidas** (`valido = False`; **não** levantam exceção; retornam uma forma do catálogo com aproximação):

- \(H \le 0\) ou \(D_{\max} \le 0\);
- qualquer um dos cinco números negativo;
- \(h_{\max} > H\).

\(D_b = 0\) ou \(D_0 = 0\) **são válidos** (ponta ou boca fechada). A razão que dividiria por zero fica finita (0), nunca \(\infty\).

### 12.2 Índices adimensionais

\[
i_H = \frac{H}{D_{\max}},\qquad
i_M = \mathrm{clip}\!\left(\frac{h_{\max}}{H},\; 0,\; 1\right),\qquad
r_b = \frac{D_b}{D_{\max}},\qquad
r_0 = \frac{D_0}{D_{\max}}.
\]

(Se \(D_{\max}=0\) ou \(H=0\), o índice correspondente vale 0 — caso já marcado inválido.)

Leitura:

- \(i_H\) — peça baixa e larga (disco) ou alta e estreita;
- \(i_M\) — barriga em baixo (pera / ovo), no meio (globo / elipsóide) ou em cima (ovo invertido);
- \(r_b\) — boca estreita em relação ao bojo.

### 12.3 Proximidade numérica («perto»)

Dois comprimentos \(a\) e \(b\) contam como quase iguais se

\[
|a-b| \le \max\bigl(0{,}12\cdot\max(|a|,|b|,10^{-9}),\; 0{,}15\bigr).
\]

Isto é: 12 % do maior, com piso de \(0{,}015\,\mathrm{cm}\). Notação abaixo: \(a \approx b\).

Simetria boca–base: \(D_b \approx D_0\). Barriga a meio: \(0{,}42 \le i_M \le 0{,}58\).

### 12.4 Árvore de decisão (`classificarForma`) — ordem obrigatória

O primeiro ramo verdadeiro encerra a decisão. Os ramos seguintes **não** são avaliados.

**1. Discoide.** Se \(i_H < 0{,}28\) → **Discoide**.

**2. Perfil Reto** (inclui `Retilineo` / `linear`). Ponta na base:

\[
D_0 \le \max\bigl(0{,}08\cdot\max(D_b, D_{\max}),\; 0{,}15\bigr).
\]

- ponta **e** \(D_b \approx D_{\max}\) → **Cônico**;
- \(D_b \approx D_{\max}\) **e** \(D_0 \approx D_{\max}\) → **Cilíndrico**;
- senão, se o maior diâmetro está na borda (\(h_{\max} \approx H\) ou \(D_b \approx D_{\max}\)) ou na base (\(h_{\max} \approx 0\) ou \(D_0 \approx D_{\max}\)), sem ponta e com \(D_b \not\approx D_0\) → **Tronco-Cônico**;
- senão, se \(D_{\max} > 1{,}12\,D_b\) **e** \(D_{\max} > 1{,}12\,D_0\) **e** \(0{,}38 \le i_M \le 0{,}62\) → **Bicônico (Cone Duplo)**;
- senão → **Cilíndrico** (tubo ou fallback retilíneo).

**3. Carena no meridiano** (θ ≥ 18° no corte interpolado; a junta do perfil composto não conta como *segunda* carena):

- duas quebras distintas (além da junta) ou perfil Carenado Duplo → **Carenado Duplo**;
- uma quebra visível (incluindo só a junta), ou quebra junto do maior diâmetro, ou perfil Carenado Simples → **Carenado**.

Piriforme, ovóide e elipsóide **não** se atribuem se este ramo fechou: pera e ovo são paredes contínuas.

**4. Barriga a meio e boca simétrica à base** (\(0{,}42 \le i_M \le 0{,}58\) e \(D_b \approx D_0\)):

- \(0{,}88 \le i_H \le 1{,}18\) → **Esférico**;
- \(i_H > 1{,}18\) → **Elipsóide Vertical**;
- senão (\(i_H < 0{,}88\)) → **Elipsóide Horizontal**.

**5. Barriga baixa** (\(i_M < 0{,}42\)):

- \(i_M < 0{,}30\) **e** \(r_b < 0{,}40\) → **Piriforme**;
- senão → **Ovoide**.

**6. Barriga alta** (\(i_M > 0{,}58\)) → **Ovoide Invertido**.

**7. Restantes** (só se nenhum ramo anterior fechou — barriga a meio, boca \(\not\approx\) base). Não há classe lixeira. Ou \(i_H\) cai numa faixa com nome, ou o programa escolhe o **centro mais próximo** e marca aproximação.

Faixas com nome:

- \(0{,}22 \le i_H < 0{,}42\) → **Lenticular** (exato);
- \(0{,}70 \le i_H < 0{,}88\) → **Subglobular** (aproximação se \(r_b \ge 0{,}92\) ou \(r_0 \ge 0{,}92\));
- \(0{,}88 \le i_H \le 1{,}18\) → **Globular** (mesma regra de aproximação).

Fora dessas faixas, distância \(|i_H - \text{centro}|\) aos centros \(0{,}32\) (lenticular), \(0{,}50\) (elipsóide horizontal), \(0{,}79\) (subglobular), \(1{,}03\) (globular), \(1{,}50\) (elipsóide vertical). O menor ganha; `aproximacao = True`.

Parede reta que não casa cone, cilindro, tronco nem bicone: o mesmo princípio sobre os quatro diâmetros, sempre com aproximação. Perfil composto **não** empurra sozinho para globular.

A planta **Quadrangular** não entra nesta árvore: `classificar()` sobrescreve a forma principal para **Quadrangular** depois de `classificarForma`.

### 12.5 Por que esta árvore e não só pontuação

A pontuação da 1.ª versão (seção 12.6) **soma** créditos em várias formas ao mesmo tempo; o vencedor pode não coincidir com a silhueta analítica (um cone pontiagudo também “parece” tronco-cônico; um disco também “parece” lenticular). A árvore **exclui** ramos: \(i_H < 0{,}28\) é disco, ponto; perfil reto com ponta e \(D_b \approx D_{\max}\) é cônico, ponto. Os nove casos ideais da seção 18.1 existem precisamente para travar essa exclusão.

A matemática é exata **depois** de se fixarem os limiares. Os limiares (\(0{,}28\), \(0{,}42\), \(0{,}58\), \(0{,}88\), \(1{,}18\), \(0{,}30\), \(0{,}40\), 12 %, \(0{,}015\,\mathrm{cm}\)) são a definição operacional do catálogo neste programa. Alterá-los muda a classificação; por isso estão escritos aqui e testados.

### 12.6 Pontuação auxiliar (`_score_par`) — segunda forma e aproximação

Todas as 19 formas começam com 0. Os acréscimos **somam-se**. “Perfil reto” nesta tabela significa Perfil geométrico = Reto, **ou** Composto com os dois trechos Reto.

| Condição | Forma que recebe pontos | Pontos |
| --- | --- | --- |
| Planta Quadrangular | Quadrangular | +8,0 |
| Diâmetro da cintura > 0 e menor que 92 % do menor entre borda, base e maior diâmetro | Hiperboloide | +6,0 |
| Segunda quebra visível (seção 7) | Carenado Duplo | +7,2 |
| Senão: perfil Carenado Simples/Duplo **ou** campos da carena preenchidos | Carenado | +6,5 |
| Três medições extras preenchidas | Escalonado | +1,5 |
| \(i_H < 0{,}22\) | Discoide | +6,0 |
| \(0{,}22 \le i_H < 0{,}42\) | Lenticular | +4,5 se o perfil for Convexo, Côncavo ou Sigmoide; senão +3,0 |
| \(0{,}22 \le i_H < 0{,}42\) | Discoide | +2,0 |
| Altura, borda e base todas “perto” do maior diâmetro | Esférico | +7,0 |
| Perfil reto **e** o menor entre borda e base \(\le \max(0{,}08\cdot\text{maior},\; 0{,}15)\) | Cônico | +6,5 |
| Perfil reto **e** borda e base “perto” do maior diâmetro | Cilíndrico | +6,5 |
| Perfil reto, maior diâmetro “perto” do maior entre borda e base, e borda **não** perto da base | Tronco-Cônico | +6,0 |
| Perfil reto, maior diâmetro > 12 % acima da borda **e** da base, e \(0{,}38 \le i_M \le 0{,}62\) | Bicônico (Cone Duplo) | +6,0 |
| \(i_M < 0{,}36\) e \(r_b < 0{,}50\) | Piriforme | +6,8 |
| \(i_M < 0{,}42\) e \(r_b < 0{,}50\) | Ovoide | +3,2 |
| \(i_M < 0{,}42\) e \(r_b \ge 0{,}50\) | Ovoide | +5,0 |
| \(i_M > 0{,}58\) | Ovoide Invertido | +5,2 |
| Barriga a meio (\(0{,}42 \le i_M \le 0{,}58\)) e \(i_H > 1{,}18\) | Elipsóide Vertical | +5,8 |
| Barriga a meio e \(i_H < 0{,}88\) | Elipsóide Horizontal | +5,8 |
| Borda e base ambas < 92 % do maior diâmetro, e \(0{,}88 \le i_H \le 1{,}18\) | Globular | +5,5 |
| Idem | Subglobular | +3,2 |
| Borda e base < 92 % do maior diâmetro, e \(0{,}70 \le i_H < 0{,}88\) | Subglobular | +5,0 |
| Idem | Elipsóide Horizontal | +3,0 |
| Composto: bojo Convexo e pescoço Reto | Globular | +2,0 |
| Idem | Cilíndrico | +2,5 |
| Composto: bojo Reto e pescoço Convexo | Cilíndrico | +2,0 |

Se altura total ou maior diâmetro forem \(\le 0\), a pontuação cai em Elipsóide Vertical com 0,2 (caso degenerado).

`classificar()` toma a forma principal de `classificarForma` (salvo Quadrangular). Seja \(S_1\) a pontuação **dessa** forma na tabela acima e \(S_2\) a maior pontuação de um nome diferente.

- **Aproximação** se \(S_1 < 4{,}5\) ou se `classificarForma` retornou `valido = False`.
- **Forma secundária** (no máximo duas designações) se

\[
S_2 \ge 0{,}72\,S_1,\qquad
S_2 \ge 3{,}5,\qquad
\text{o segundo nome é diferente do primeiro}.
\]

No cadastro, a segunda sugestão só é copiada para o campo visível quando o perfil geométrico é **Composto** (bojo + pescoço é o caso típico de duas designações, por exemplo Globular e Cilíndrico). O usuário pode preencher a segunda forma mesmo assim.

A forma **confirmada** (e a segunda confirmada) é o que o usuário deixa na tela ao gravar. É esse valor que o relatório usa.

### 12.7 Leitura didática das formas mais comuns

- **Esférico:** barriga a meio, boca simétrica à base, \(0{,}88 \le i_H \le 1{,}18\).
- **Globular:** \(0{,}88 \le i_H \le 1{,}18\), quando a árvore não fechou antes (esfera / elipsóide / ovo). Se a boca ou a base não fecham o bojo (\(r_b\) ou \(r_0 \ge 0{,}92\)), o nome permanece e a ficha marca aproximação.
- **Subglobular:** o mesmo, com \(0{,}70 \le i_H < 0{,}88\).
- **Piriforme:** barriga muito baixa (\(i_M < 0{,}30\)) e boca estreita (\(r_b < 0{,}40\)), **sem** quebra de tangente no meridiano.
- **Ovoide / Ovoide Invertido:** barriga baixa (\(i_M < 0{,}42\)) ou alta (\(i_M > 0{,}58\)), sem exigir a boca tão estreita quanto a pera, parede contínua.
- **Elipsóide Vertical / Horizontal:** no ramo próprio, barriga a meio e boca \(\approx\) base; \(i_H\) decide o eixo maior; parede contínua. Fora desse ramo só aparecem se forem o centro de \(i_H\) mais próximo (tigela \(\approx 0{,}50\) ou jarro \(\approx 1{,}50\)), sempre com aproximação.
- **Cilíndrico:** parede reta e os três diâmetros quase iguais (ou tubo: fallback retilíneo). Um pescoço que **afina** não é cilíndrico.
- **Cônico / Tronco-Cônico / Bicônico:** parede reta; ponta na base, dois diâmetros distintos sem ponta, ou barriga angular no meio (o encontro de dois cones tem nome próprio, não “Carenado”).
- **Discoide / Lenticular:** peça muito baixa (\(i_H < 0{,}28\) no primeiro ramo; lenticular só se esse ramo não fechou).
- **Carenado / Carenado Duplo:** \(\theta \ge 18^\circ\) no meridiano interpolado, **antes** das silhuetas lisas. A junta do perfil composto não gera Carenado Duplo sozinha.

---

## 13. Centro de massa da casca (ponto de equilíbrio)

Não é o centro de massa do volume de líquido: é o de uma **casca fina** de revolução (a argila, se a espessura fosse uniforme e desprezível). O valor aparece na ficha do objeto (altura acima do apoio), sem marca no desenho 3D.

Cada segmento do meridiano da **parede** \((Z, R)\) contribui com a área da faixa de revolução:

\[
\Delta s = \sqrt{(\Delta Z)^2+(\Delta R)^2},\qquad
\bar{Z} = \tfrac{Z_i+Z_{i+1}}{2},\qquad
\bar{R} = \max\bigl(\tfrac{R_i+R_{i+1}}{2},\; 10^{-9}\bigr),
\]

\[
\Delta A_{\mathrm{parede}} = 2\pi\,\bar{R}\,\Delta s.
\]

O **fundo** entra à parte, de forma explícita, no **mesmo** referencial da parede (\(Z = 0\) no ponto de contato com a mesa: centro na convexa, anel na côncava):

- base **reta**: disco plano de área \(\pi R_b^2\) no plano de apoio (\(Z = 0\)), onde \(R_b\) é o raio interno na base;
- base **côncava** ou **convexa**: superfície da calota parabólica, \(2\pi \bar{R}\,\Delta s\) ao longo da geratriz do fundo; as alturas \(\bar{Z}\) das faixas da calota são as do meridiano \(z(r)\) da seção 8, **sem** somar de novo a translação \(+s\) da parede.

\[
Z_{\mathrm{cm}} = \frac{
  \sum \bar{Z}\,\Delta A_{\mathrm{parede}}
  + Z_{\mathrm{fundo}}\,A_{\mathrm{fundo}}
}{
  \sum \Delta A_{\mathrm{parede}}
  + A_{\mathrm{fundo}}
}.
\]

(No disco, \(Z_{\mathrm{fundo}} = 0\) e \(A_{\mathrm{fundo}} = \pi R_b^2\). Na calota, o momento e a área vêm da soma das faixas da parábola.)

Comentário de estabilidade (só texto na ficha):

- base **reta**: apoio plano no anel (ou disco);
- base **côncava**: apoio no anel, fundo reentrante;
- base **convexa**: se \(Z_{\mathrm{cm}} < \rho\), tendência a recuperar a vertical; se \(Z_{\mathrm{cm}} > \rho\), equilíbrio mais instável ao inclinar (\(\rho\) na seção 8).

---

## 14. Relatório por sítio

O relatório (HTML, PDF via Chrome/Chromium ou wkhtmltopdf, e CSV) agrupa os objetos de **um** nome de sítio.

- **Ocorrência das formas:** usa a forma confirmada (a primeira, se houver duas). Ordena da mais frequente para a menos; percentual \(100\cdot n / N\), uma casa decimal com vírgula.
- **Lista dos objetos:** número do desenho, forma (as duas, se houver, ligadas por “ / ”), tamanho, altura total, maior diâmetro da peça, volume, se a sugestão foi aproximação.
- **Resumo por volume:** contagem nas faixas da seção 10.

Não entram no relatório: proveniência, fotografia, desenho de campo nem bibliografia.

---

## 15. Persistência

Banco SQLite no diretório do programa (`ceraform.sqlite`). A tabela chama-se `vasos` (um objeto por linha). Cada gravação atualiza `updated_at`. O campo `forma_alterada_manualmente` fica verdadeiro quando o usuário confirma uma forma diferente da sugestão do algoritmo (não há histórico de versões: vale o valor atual).

As três medições extras (1/4, 1/2 e 3/4 da altura total) gravam-se como texto de pares `altura, diâmetro` (uma por linha), calculados a partir da altura total. Outros pares já gravados (por exemplo uma amostra de pescoço que não seja uma dessas três cotas) **permanecem** ao salvar (`amostras_exceto_fracoes` + `texto_amostras_gravadas`). A junção bojo–pescoço e as carenas têm colunas próprias.

---

## 16. Mapa rápido código ↔ regra

| Tema | Arquivo |
| --- | --- |
| Catálogo de 19 formas, perfis, bases, plantas, faixas | `ceraform/constantes.py` |
| Estações, PCHIP, Hermite, composto, quebras, base, revolução | `ceraform/perfil.py` |
| Inferência de forma (`classificarForma`, pontuação auxiliar) | `ceraform/classificar.py` |
| Volume analítico (`calcular_volume`) e tamanho | `ceraform/volume.py` |
| Provas unitárias da forma | `tests/test_classificador.py` |
| Provas unitárias do volume analítico | `tests/test_volume.py` |
| Provas PCHIP / Hermite / perfil | `tests/test_perfil.py` |
| Provas das quebras de 18° | `tests/test_quebras.py` |
| Provas do centro de massa da casca | `tests/test_centro_massa.py` |
| Provas da planta quadrangular e do volume trapezoidal | `tests/test_planta.py` |
| Provas das faixas de tamanho | `tests/test_tamanho.py` |
| Provas do relatório HTML / CSV / PDF | `tests/test_relatorio.py` |
| Sólido oco 3D (malha, PBR/off-screen, órbita/zoom) e planta | `ceraform/vista_solido.py` |
| Corte 2D (técnico / Publicação / PDF milimetrado) | `ceraform/visual_2d.py` |
| Relatório | `ceraform/relatorio.py` |
| Tela de cadastro, ficha 3D e PNG do sólido | `ceraform/ui_desktop.py` |
| PDF «Como funciona» (gerado do Markdown; o botão na tela Sobre abre este PDF) | `documentacao/como_o_sistema_funciona.pdf` |
| Times New Roman 12 (interface e PNG da ficha) | `ceraform/fonte.py` |
| Arquitetura e fluxo (Draw.io e SVG; botão na tela Sobre) | `documentacao/arquitetura_e_fluxo.drawio` |
| Decisões fechadas | `decisoes_requisitos.txt` |
| Provas do PNG da ficha 3D (nome do sítio sem truncar) | `tests/test_png_ficha.py` |
| Prova da elevação de publicação (tigela rasa) | `tests/test_elevacao_publicacao.py` |
| Provas do tracejado da espessura da parede no corte 2D | `tests/test_espessura_2d.py` |

---

## 17. Como conferir com um exemplo

Tome um objeto globular composto (bojo + pescoço).

1. Confira se as cotas do núcleo estão preenchidas (altura, diâmetros da borda e máximo > 0; diâmetro da base ≥ 0).
2. O meridiano deve passar **exatamente** pela base, pelo maior diâmetro, pela junção e pela borda.
3. Se o trecho do pescoço **afinar** (diâmetro da junção ≠ diâmetro da borda) e o perfil desse trecho for Convexo, a segunda forma **não** deve ser Cilíndrico — cilindro exige diâmetros quase iguais e parede reta.
4. O volume na ficha deve coincidir, a menos de arredondamento, com a integral trapezoidal do perfil interno (seção 9.2). Os sólidos ideais (cilindro, cone, esfera) devem coincidir com `calcular_volume` (seção 9.1 e 18.3).
5. A forma na lista e no PDF é a **confirmada**, não a sugestão, se o usuário tiver corrigido.

A conferência **numérica** da inferência de forma, do volume, do perfil, das quebras, do centro de massa, da planta, das faixas de tamanho, do relatório, da ficha PNG e do sólido 3D está na seção 18 (103 provas). A validação arqueológica do catálogo (nomes no campo) foi conferida e validada junto à Dra. Cláudia: os limiares desta página são os que o programa usa hoje.

---

## 18. Relatório das provas unitárias (todas OK)

As suítes estão em `tests/`. Comando (a partir de `/home/luis/CeraForm`):

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Resultado da suíte: **103 provas** em `tests/` (incluindo fundo arredondado com diâmetro da base 0 cm, cotas a um quarto / metade / três quartos da altura total, junção bojo–pescoço com barriga perto da borda, PNG da ficha sem truncar o nome do sítio, carena antes de silhueta lisa, vizinho mais próximo sem classe lixeira, e sólido 3D com casca oca e zoom persistente). Nenhuma prova de validade deve levantar exceção em dados degenerados; medidas inválidas retornam `valido = False` e uma forma do catálogo.

Unidades: cotas em **centímetro**; volume analítico em **centímetro cúbico** (1 cm³ = 1 mL; conversão a litro só na ficha, seção 9.1); volume da malha em **litro**.

### 18.1 Inferência de forma — nove silhuetas ideais

Função sob teste: `classificarForma`. Cada linha é um sólido geométrico cuja classificação **tem** de coincidir com o nome da coluna «Forma». Os índices da seção 12.2 explicam o ramo da árvore.

| # | Teste | \(H\) | \(D_{\max}\) | \(D_0\) | \(D_b\) | \(h_{\max}\) | Perfil | Forma | Porquê (ramo) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `test_esfera_perfeita` | 100 | 100 | 30 | 30 | 50 | Convexo | Esférico | \(i_H=1\), \(i_M=0{,}50\), \(D_b\approx D_0\) |
| 2 | `test_elipsoide_vertical` | 150 | 100 | 40 | 40 | 75 | Convexo | Elipsóide Vertical | \(i_H=1{,}50>1{,}18\), barriga a meio |
| 3 | `test_elipsoide_horizontal` | 80 | 160 | 60 | 60 | 40 | Convexo | Elipsóide Horizontal | \(i_H=0{,}50<0{,}88\), barriga a meio |
| 4 | `test_cilindro_puro` | 120 | 100 | 100 | 100 | 60 | Retilineo | Cilíndrico | reto e \(D_b\approx D_{\max}\approx D_0\) |
| 5 | `test_cone_simples` | 120 | 100 | 0 | 100 | 120 | Retilineo | Cônico | reto, ponta \(D_0=0\), \(D_b\approx D_{\max}\) |
| 6 | `test_tronco_conico` | 100 | 120 | 60 | 120 | 100 | Retilineo | Tronco-Cônico | reto, \(D_{\max}\) na borda, \(D_b\not\approx D_0\) |
| 7 | `test_ovoide_direto` | 140 | 100 | 50 | 40 | 45 | Convexo | Ovoide | \(i_M=0{,}321<0{,}42\), não piriforme |
| 8 | `test_ovoide_invertido` | 140 | 100 | 40 | 50 | 95 | Convexo | Ovoide Invertido | \(i_M=0{,}679>0{,}58\) |
| 9 | `test_discoide` | 30 | 150 | 80 | 150 | 15 | Convexo | Discoide | \(i_H=0{,}20<0{,}28\) |

Notas de integridade:

- A esfera de teste **não** tem boca e base iguais ao maior diâmetro (3 cm contra 10 cm): o ramo 3 exige simetria boca–base e \(i_H\) na faixa esférica, não a bola fechada. O volume da esfera fechada está na prova 23 (seção 18.3).
- O cone usa \(D_0=0\) de propósito: divisão por zero está proibida (razões finitas).
- `Retilineo` é sinônimo de Reto; a árvore não depende da grafia da tela.

### 18.2 Inferência de forma — borda, robustez e último recurso

| # | Teste | Entrada relevante | Esperado |
| --- | --- | --- | --- |
| 10 | `test_d0_zero_base_pontiaguda` | \(D_0=0\), reto, demais como o cone #5 | razões finitas; **Cônico**; `valido=True` |
| 11 | `test_db_zero_borda_fechada` | \(H=100\), \(D_{\max}=80\), \(D_b=0\), \(D_0=50\), \(h_{\max}=50\), Convexo | razões finitas; forma do catálogo; `valido=True`; sem exceção |
| 12 | `test_d0_e_db_zero` | \(D_b=D_0=0\), Convexo | razões finitas (nunca \(\infty\)); `valido=True` |
| 13 | `test_tubular` | \(H=300\), \(D_{\max}=D_b=D_0=40\), \(h_{\max}=150\), Retilineo | **Cilíndrico** |
| 14 | `test_prato_plano` | \(H=8\), \(D_{\max}=200\), \(D_b=200\), \(D_0=180\), \(h_{\max}=4\), Convexo | **Discoide** (\(i_H=0{,}04<0{,}28\)) |
| 15 | `test_bojo_extremo_superior` | \(h_{\max}=H=140\), Convexo, ovoide invertido #8 | **Ovoide Invertido** (\(i_M=1\)) |
| 16 | `test_bojo_extremo_inferior` | \(h_{\max}=0\), Convexo, ovoide #7 | **Ovoide** (\(i_M=0\); \(r_b=0{,}40\) não é \(<0{,}40\), logo não Piriforme) |
| 17 | `test_h_zero_invalido` | \(H=0\) | `valido=False`; forma do catálogo |
| 18 | `test_dmax_zero_invalido` | \(D_{\max}=0\) | `valido=False`; forma do catálogo |
| 19 | `test_valores_negativos_invalidos` | cada um de \(H, D_{\max}, D_b, D_0, h_{\max}\) negativo (5 subcasos) | `valido=False`; forma do catálogo |
| 20 | `test_hmax_maior_que_h_invalido` | \(h_{\max}=150>H=100\) | `valido=False`; forma do catálogo |
| 20a | `test_piriforme_parede_lisa` | barriga baixa, boca estreita, Convexo | **Piriforme** (sem quebra) |
| 20b | `test_tb031_quebra_nao_e_pera` | Composto reto+convexo, \(\theta\approx 77^\circ\) | **Carenado**, não Piriforme |
| 20c | `test_bicone_reto_nao_vira_carenado` | dois cones, perfil reto | **Bicônico (Cone Duplo)** |
| 20d | `test_etiq_67083_horizontal_aproximado` | tigela \(i_H=0{,}43\), boca aberta, base 0 | **Elipsóide Horizontal** (aproximação; centro 0,50) |
| 20e | `test_166422_subglobular_aproximado` | \(i_M=0{,}49\), \(i_H=0{,}79\), Côncavo | **Subglobular** (aproximação; boca quase o bojo) |
| 20f | `test_761305_ovoide_invertido_exato` | \(i_M=0{,}94\) | **Ovoide Invertido** (exato) |
| 20g | `test_ih_1_25_mais_perto_de_globular` | \(i_H=1{,}25\), boca 0 | **Globular** (aproximação; mais perto de 1,03 que de 1,50) |
| 20h | `test_ih_1_50_elipsoide_vertical_aproximado` | \(i_H=1{,}50\), boca ≉ base | **Elipsóide Vertical** (aproximação) |
| 20i | `test_elipsoide_limpo_nao_e_aproximacao` | caso-teste #2 | **Elipsóide Vertical** sem aproximação |


As provas 17–20 garantem que dados impossíveis **não** quebram o cadastro: o usuário vê uma forma aproximada marcada inválida, em vez de um erro de execução.

### 18.3 Volume analítico — quatro sólidos de revolução

Função sob teste: `calcular_volume` (seção 9.1). Os volumes esperados são as fórmulas clássicas, em \(\mathrm{cm}^3\). A suíte também confere \(V_{\mathrm{mL}}=V_{\mathrm{cm}^3}\) e \(V_{\mathrm{L}}=V_{\mathrm{cm}^3}/10^3\).

| # | Teste | Geometria | Fórmula esperada | Valor simbólico |
| --- | --- | --- | --- | --- |
| 21 | `test_cilindro_100x100` | cilindro \(H=100\), \(D=100\), Retilineo | \(\pi R^2 H\) | \(\pi\cdot 50^2\cdot 100\) |
| 22 | `test_cone_120x100` | cone \(H=120\), \(D_{\mathrm{borda}}=100\), \(D_0=0\), \(h_{\max}=120\) | \(\pi R^2 H/3\) | \(\pi\cdot 50^2\cdot 120/3\) |
| 23 | `test_esfera_100` | esfera \(\varnothing=100\), Convexo, \(D_b=D_0=0\), \(h_{\max}=50\) | \(\frac{4}{3}\pi R^3\) | \(\frac{4}{3}\pi\cdot 50^3\) |
| 24 | `test_desconto_espessura_parede` | cilindro do #21 com parede \(t=5\,\mathrm{cm}\) | \(\pi (R-t)^2 (H-t)\) | \(\pi\cdot 45^2\cdot 95\); e \(V_{\mathrm{oco}}<V_{\mathrm{cheio}}\) |

A esfera #23 usa dois hemisférios (zona esférica da seção 9.1): \(3a^2+3b^2+h^2\) em cada metade com \(a=0\), \(b=50\), \(h=50\) recupera \(\frac{2}{3}\pi R^3\) por metade, logo \(\frac{4}{3}\pi R^3\).

O desconto da parede (#24) aplica \(D'=D-2t\) e \(H'=H-t\) **antes** da integração: a cavidade interna de um tubo de parede 5 cm não é o cilindro exterior.

### 18.4 PCHIP, Hermite, cotas a 1/4–3/4 e junção — dezessete provas (`tests/test_perfil.py`)

Funções: `_hermite_cubico`, `_pchip_perfil`, `_pchip_derivadas`, `perfil_raios`, `diametros_fracao`.

| # | Teste | Esperado |
| --- | --- | --- |
| 25 | `test_hermite_recupera_os_extremos_do_intervalo` | \(R(Z_i)=R_i\) e \(R(Z_{i+1})=R_{i+1}\) |
| 26 | `test_hermite_linear_quando_derivadas_sao_a_secante` | se \(d_i=d_{i+1}=\delta\), \(R(Z)\) é a reta secante |
| 27 | `test_pchip_passa_exactamente_pelas_estacoes` | a curva passa pelos pontos medidos |
| 28 | `test_pchip_nao_ultrapassa_o_maximo_local` | Fritsch–Carlson: sem overshoot além do maior raio do intervalo |
| 29 | `test_pchip_monotono_em_troco_crescente` | raios crescentes nas estações ⇒ \(R(Z)\) não desce |
| 30 | `test_derivada_nula_quando_a_secante_muda_de_sinal` | \(\delta_{i-1}\cdot\delta_i\le 0\) ⇒ \(d_i=0\) |
| 31 | `test_pico_horizontal_no_maior_diametro` | \(dR/dZ=0\) na estação do maior diâmetro |
| 32 | `test_perfil_reto_e_linear_entre_estacoes` | tronco \(R_{\mathrm{base}}=20\), \(R_{\mathrm{borda}}=40\), meia altura \(R=30\) |
| 33 | `test_perfil_convexo_passa_pelo_maior_diametro` | em \(Z=H_{\max}\), \(R=D_{\max}/2\); tangente quase horizontal |
| 33a | `test_diametros_fracao_nao_confundem_pescoco_com_tres_quartos` | junção a 8,0 cm não preenche o campo de três quartos |
| 33b | `test_diametros_fracao_reconhecem_cotas_gravadas` | recupera os três diâmetros gravados |
| 33c | `test_base_zero_respeita_diametro_a_um_quarto_da_altura` | fundo em calota passa pela cota abaixo da barriga |
| 33d | `test_base_zero_respeita_diametro_a_tres_quartos_da_altura` | cota acima da barriga com base 0 cm |
| 33e | `test_anel_na_base_respeita_as_tres_fracoes` | com anel, as três frações entram no PCHIP |
| 33f | `test_tigela_base_zero_respeita_fracao_abaixo_da_borda` | tigela (\(H_{\max}\) na borda): 1/4 e 1/2 entram |
| 33g | `test_juncao_com_barriga_perto_da_borda_e_base_zero` | ovoide invertido, base 0: a junção não some |
| 33h | `test_juncao_em_peca_com_anel_e_perfil_convexo` | junção entra sem exigir perfil Composto |

### 18.5 Quebras de 18° — sete provas (`tests/test_quebras.py`)

Função: `quebras_meridiano`. Há carena se o ângulo interior \(\theta \ge 18^\circ\).

| # | Teste | Esperado |
| --- | --- | --- |
| 34 | `test_parede_recta_sem_quebra` | cilindro: lista vazia |
| 35 | `test_angulo_recto_e_quebra` | viragem \(\gt 80^\circ\): uma quebra |
| 36 | `test_dezassete_graus_nao_e_carena` | \(17^\circ\): sem quebra |
| 37 | `test_dezoito_graus_e_carena` | \(18{,}01^\circ\): uma quebra (ulp de \(\arccos\) abaixo de \(18^\circ\) exatos) |
| 38 | `test_dezanove_graus_e_carena` | \(19^\circ\): uma quebra |
| 39 | `test_duas_quebras_distintas` | dois vértices angulosos: duas quebras |
| 40 | `test_menos_de_tres_estacoes_sem_quebra` | dois pontos: lista vazia |

### 18.6 Centro de massa da casca e fundo arredondado — treze provas (`tests/test_centro_massa.py`)

Funções: `centro_massa_casca`, `curva_base`, `raio_curvatura_base`, `perfil_arco_borda_a_borda`, `perfil_circulo_elipse_fechado`, `perfil_raios` / `meridiano_com_base` (base 0 cm).

| # | Teste | Fórmula / esperado |
| --- | --- | --- |
| 41 | `test_cilindro_com_fundo_plano` | parede \(2\pi R H\) em \(Z=H/2\) + disco \(\pi R^2\) em \(Z=0\): \(Z_{\mathrm{cm}}=H^2/(2H+R)\) |
| 42 | `test_parede_sozinha_sem_area_de_fundo_degenerada` | raio do fundo 0: \(Z_{\mathrm{cm}}=H/2\) |
| 43 | `test_base_convexa_desloca_o_cm_para_cima_da_reta` | calota parabólica: \(Z_{\mathrm{cm}}\) maior que na base reta |
| 44 | `test_raio_de_curvatura_da_base_convexa` | \(\rho=R_b^2/(2s)=2{,}5\,R_b\) com \(s=0{,}20\,R_b\) |
| 45 | `test_base_reta_sem_raio_de_curvatura` | retorna `None` |
| 46 | `test_sagita_da_base_concava` | no centro \(z=s\); no anel \(z=0\) |
| 46a | `test_base_concava_diametro_zero_fecha_no_eixo` | tigela \(D_{\max}=D_b\), base 0: arco/elipse, sem pontinha |
| 46b | `test_base_concava_zero_respeita_maior_diametro` | elipse pelo \(D_{\max}\) em \(H_{\max}\) e pela borda; fundo arredondado |
| 46c | `test_parede_reta_base_zero_permanece_cone` | perfil reto + base 0: geratriz cónica |
| 46d | `test_arco_profundo_sem_salto_vertical` | curva auxiliar \(H > R\): semi-elipse contínua |
| 46e | `test_qmn_0003_barriga_ligeiramente_maior_que_borda` | 23,5 cm em \(Z=19\), borda 21: não tratar como tigela |
| 46f | `test_base_zero_respeita_amostra_do_pescoco` | amostra acima da barriga com base 0 cm |
| 46g | `test_juncao_bojo_pescoco_sem_canto` | junção arredondada: sem quebra de 18° |

### 18.7 Planta quadrangular e volume da malha — nove provas (`tests/test_planta.py`)

Funções: `_xy_secao`, `area_secao_mm2`, `volume_litros`, `volume_ate_altura_litros`.

| # | Teste | Esperado |
| --- | --- | --- |
| 47 | `test_eixos_do_quadrado` | \(\theta=0\): \((R,0)\); \(\theta=\pi/2\): \((0,R)\) |
| 48 | `test_canto_a_quarenta_e_cinco_graus` | quadrado: \((R,R)\), não a elipse |
| 49 | `test_circular_a_quarenta_e_cinco_graus_nao_e_o_canto` | círculo: \(R/\sqrt{2}\) nos dois eixos |
| 50 | `test_rectangulo_com_escala_sy` | em \(\theta=\pi/2\), \(y=R\,s_y\) |
| 51 | `test_area_quadrangular_nao_e_a_elipse` | \(A=4R^2\) contra \(\pi R^2\) |
| 52 | `test_volume_prisma_quadrangular` | \(V=4R^2 H\) |
| 53 | `test_cilindro_coincide_com_pi_r2_h` | trapézio da malha = \(\pi R^2 H\) (bate com a prova 21) |
| 54 | `test_cone_trapezio_aproxima_pi_r2_h_sobre_3` | malha de 241 nós \(\approx \pi R^2 H/3\) |
| 55 | `test_corte_a_85_por_cento_inclui_o_limite` | \(V_{85\%}=\pi R^2\cdot 0{,}85 H\), mesmo se 0,85 H cair entre nós |

### 18.8 Faixas de tamanho — sete provas (`tests/test_tamanho.py`)

Funções: `faixa_tamanho`, `observacao_volume`, `rotulo_tamanho`. Intervalos \([a,b)\).

| # | Teste | Volume (L) | Tamanho | Observação |
| --- | --- | --- | --- | --- |
| 56 | `test_pequeno_abaixo_de_0_150` | 0,149 | Pequeno | abaixo de 0,150 L |
| 57 | `test_pequeno_no_limiar_0_150` | 0,150 | Pequeno | — |
| 58 | `test_pequeno_ate_1_litro_exclusive` | 0,999 / 1,0 | Pequeno / Médio | — |
| 59 | `test_medio_ate_4_litros_exclusive` | 3,999 / 4,0 | Médio / Grande | — |
| 60 | `test_grande_ate_16_litros_exclusive` | 15,999 / 16,0 | Grande / Extra grande | — |
| 61 | `test_extra_grande_antes_de_50` | 49,999 | Extra grande | — |
| 62 | `test_extra_grande_a_partir_de_50` | 50,0 | Extra grande | a partir de 50,0 L |

### 18.9 Relatório por sítio — quatro provas (`tests/test_relatorio.py`)

Funções: `ficha_cabecalho_sitio`, `html_relatorio_sitio`, `gravar_relatorio_csv`, `html_para_pdf`. A forma na contagem é a **confirmada**, não a sugestão.

| # | Teste | Esperado |
| --- | --- | --- |
| 63 | `test_ocorrencia_usa_forma_confirmada` | 2 Globular (66,7 %) e 1 Cilíndrico (33,3 %); Ovoide sugerido não entra |
| 64 | `test_html_tem_percentual_com_virgula_e_campos_por_extenso` | «66,7 %»; altura total; número do desenho; tamanho com observação |
| 65 | `test_csv_usa_forma_confirmada_e_separador_ponto_e_virgula` | colunas por extenso; `;`; forma confirmada |
| 66 | `test_html_gravado_gera_pdf_quando_ha_conversor` | HTML sempre; se houver Chrome/Chromium/`wkhtmltopdf`, o arquivo começa por `%PDF-`; senão a conversão retorna falso **sem abortar** |

### 18.10 Ficha PNG do 3D — duas provas (`tests/test_png_ficha.py`)

Funções: `_envolver_texto_png`, `_truetype_serif` (Times 12). O nome do sítio no PNG da vista 3D não pode ser truncado.

| # | Teste | Esperado |
| --- | --- | --- |
| 67 | `test_nome_do_sitio_nao_e_cortado` | «Aldeia do Boqueirão da Serra Nova» cabe, em uma ou mais linhas, na coluna da ficha |
| 68 | `test_texto_curto_fica_numa_so_linha` | número do desenho curto permanece numa só linha |

### 18.11 Elevação de publicação — uma prova (`tests/test_elevacao_publicacao.py`)

| # | Teste | Esperado |
| --- | --- | --- |
| 69 | `test_desenha_tigela_rasa_sem_erro` | tigela com diâmetro da base 0 cm gera PNG de publicação sem erro |

### 18.12 Espessura da parede no corte 2D — quatro provas (`tests/test_espessura_2d.py`)

| # | Teste | Esperado |
| --- | --- | --- |
| 70 | `test_offset_base_zero_fecha_no_eixo` | com diâmetro da base 0 cm o tracejado externo fecha no eixo, abaixo do fundo interno |
| 71 | `test_offset_distancia_na_parede_aproxima_a_espessura` | na parede, a distância interno–externo ≈ espessura da parede |
| 72 | `test_tracejado_contorna_a_base_zero` | o corte 2D tem um único tracejado que cruza o eixo e a cota «espes. parede» |
| 73 | `test_fechamento_na_borda_e_horizontal` | o lábio termina na altura da borda, raio interno + espessura (tigela e jarro) |

### 18.13 Sólido 3D (casca, cerâmica, zoom) — seis provas (`tests/test_solido_3d.py`)

| # | Teste | Esperado |
| --- | --- | --- |
| 74 | `test_casca_interna_menor_que_a_externa` | na casca 3D o raio interno é o externo menos a espessura da parede |
| 75 | `test_espessura_vazia_usa_dois_milimetros` | campo vazio → 0,2 cm só no desenho 3D |
| 76 | `test_malha_traz_rgb_de_engobo` | a malha PyVista traz cores RGB de argila/engobo (não é um dielétrico sem albedo) |
| 77 | `test_mostrar_nao_zera_o_zoom` | `mostrar()` reconstrói a peça e conserva zoom e azimute |
| 78 | `test_fator_zoom_roda_windows_e_x11` | a roda do mouse amplia e reduz no Windows/Wine (MouseWheel e HIWORD) e no X11 (Button-4/5) |
| 79 | `test_cabecalho_sem_bom_nem_iguais_soltos` | `CABECALHO.txt` sem BOM; o Sobre mostra autoria e licença; no Windows o exe remove BOM, CR e linhas em branco repetidas |

### 18.14 Mecanismo de integridade

Alterar um limiar da seção 12.4 sem atualizar `tests/test_classificador.py` quebra as provas 1–16 de propósito. O mesmo vale para os 18° (provas 36–38), para as faixas de tamanho (56–62) e para \(Z_{\mathrm{cm}}=H^2/(2H+R)\) (prova 41): o teste é o contrato da fórmula. A ficha na tela usa o volume trapezoidal da malha (provas 53–55); o volume analítico das provas 21–24 é o de `calcular_volume`. Num cilindro ou cone ideais os dois coincidem.
