# 09 · Moonlight direto na TV Samsung (plano B)

## Objetivo

Jogar na TV sem comprar nada, instalando o Moonlight no Tizen pelo Modo Desenvolvedor.

## Pré-requisitos

- TV Samsung com Tizen 5.5 ou mais novo. Testado numa AU7700 (2021, Tizen 6.0). Tizen 7+ (2023 em diante) exige conta Samsung para assinar o app.
- Um computador com Docker na mesma rede.

## Passos

1. **Na TV:** Apps → digite `12345` no controle → Developer Mode **On** → IP do computador que vai instalar → reinicie a TV.
2. **No computador**, com o IP da TV. A imagem do projeto OneLiberty/moonlight-chrome-tizen já traz o app e um certificado:

```bash
docker run --rm --platform linux/amd64 ghcr.io/oneliberty/moonlight-chrome-tizen:samsung_wasm \
  bash -lc 'export PATH=$PATH:~/tizen-studio/tools:~/tizen-studio/tools/ide/bin; sdb connect IP-DA-TV; tizen install -n Moonlight.wgt'
```

3. No app da TV: **Add Host → IP-DO-PC** → PIN no painel do Sunshine.
4. Configure **H.264, 30 Mbps, 1080p, 60 FPS**.

## Verificação

- O app abre e transmite o Desktop ou o Steam Big Picture.

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| HEVC pisca preto | Decodificador do app nessa TV | Use H.264 |
| Cores desbotadas | O app não trata a faixa de cor | Compense nos ajustes de imagem, ou use o Fire Stick |
| Leve atraso | O Modo Jogo da Samsung só existe em entradas HDMI | Fire Stick ([08](08-fire-tv.md)) |
| O app sumiu após atualizar a TV | A atualização de firmware apaga apps de desenvolvedor | Reinstale do mesmo jeito |
| Descoberta automática não acha o PC | — | Add Host pelo IP |

**Free My TV** (tela inicial sem propaganda, `simbasjungles/free-my-tv`): suporta Tizen 2015+ e pode ser instalado do mesmo jeito. No Fire TV, ele é só mais um app, porque a Amazon trava o launcher.
