# Método recursivo de criação

Este documento registra o processo de criação musical descrito por FEZ. Ele integra o acervo artístico: não é apenas documentação técnica.

## Princípio

O processo começa com uma **semente melódica, rítmica, textual ou conceitual**. Essa semente é modulada entre código, prompt e coprodução com modelos generativos até que uma possibilidade musical coerente com a intenção artística consiga emergir.

## Ciclo de trabalho

```text
semente humana
→ prompt e tags
→ geração no modelo
→ escuta e seleção
→ descarte ou modulação
→ reescrita e ajuste fonético
→ nova geração
→ separação de stems
→ retorno à DAW
→ edição, execução e mixagem
→ nova semente
```

O ciclo pode se repetir muitas vezes. A geração não encerra a composição: ela fornece matéria para novas decisões humanas.

## Registro de MOSTRE

O manifesto preserva este resumo operacional do processo:

```python
instrumental = gerar(Suno, base, tags="spoken word, slam")
versoes = [gerar() for _ in range(20)]  # iteração
letra = ajustar_fonetica(letra_original, beat)
stems = separar(Moises, versao_escolhida)
mix = editar(DAW, stems, intervencoes_humanas)
capa = gerar_imagem(GPT, contexto_artistico)
```

O código acima funciona como registro conceitual, não como software executável. Ele explicita escolha, repetição, ajuste, separação e reconstrução.

## Formulação do projeto

Tecnologia como ponte, não como atalho. A autoria permanece nas decisões, recusas, escutas, combinações e transformações que organizam o material até a obra adquirir forma.

As tags efetivamente recuperadas das letras estão em [`suno/TAGS_E_DIRECOES.md`](suno/TAGS_E_DIRECOES.md).
