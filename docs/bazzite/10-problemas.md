# 10 · Problemas e soluções (Bazzite + streaming)

## Formato

Cada problema tem: **sintoma** → **diagnóstico** (como confirmar) → **causa** → **solução**.

---

## Erro 503 ao conectar no Moonlight

- **Diagnóstico:** `journalctl --user -u app-dev.lizardbyte.app.Sunshine -o cat | grep -E "Couldn't find monitor|Fatal"`
- **Causa:** no Modo Desktop, o KDE apagou a tela por inatividade (saída "connected" mas "disabled" em `/sys/class/drm/card*-*/enabled`).
- **Solução imediata:**

```bash
WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/$(id -u) kscreen-doctor --dpms on
```

- **Solução de fundo:** jogar pelo Game Mode, ou desligar o apagamento de tela do KDE.

## "Conexão encerrada, código -1" / erro de captura

- **Diagnóstico:** o log mostra `Couldn't connect to Wayland display: gamescope-0` no Desktop, ou o contrário, e cai para `libx264 [software]`.
- **Causa:** o Sunshine subiu num modo (Game Mode ou Desktop) e o PC trocou de modo. Ele continua com o display antigo.
- **Solução:**

```bash
systemctl --user restart app-dev.lizardbyte.app.Sunshine
```

## Imagem escura no stream

- **Diagnóstico:** o log mostra `Color coding: SDR` e a TV recebe SDR, mas `xprop -root GAMESCOPE_DISPLAY_HDR_ENABLED` (com `DISPLAY=:0`) dá `1`.
- **Causa:** o monitor ligado ao PC aceita HDR, então o Game Mode desenha em HDR. Enviada como SDR, a imagem chega escura.
- **Solução que funcionou:**
  1. Moonlight com **HEVC + HDR ligado** (HDR só funciona com HEVC). O log passa a mostrar `HDR (Rec. 2020 + SMPTE 2084 PQ)`, 10-bit.
  2. **Desligar** "forçar faixa completa de cor" no Moonlight. O log deve mostrar `Color range: MPEG`.
  3. Na Steam (Game Mode): Configurações → Tela → aumentar o **brilho do conteúdo SDR**. Isso foi o que mais clareou.
  4. Em TV de entrada (AU7700), o HDR fica mais escuro que o SDR. Com a **"Expansão do sinal de entrada" desligada** na porta HDMI do Fire Stick, a TV não anuncia HDR, o Fire Stick converte para SDR e a imagem fica mais clara.
- **O que não resolveu:** ajustar `GAMESCOPE_SDR_ON_HDR_CONTENT_BRIGHTNESS` via `xprop` (a Steam sobrescreve) e forçar `GAMESCOPE_COMPOSITE_FORCE`.

## Tela preta no stream ao desligar o HDR do Game Mode

- **Diagnóstico:** `Couldn't get drm fb for plane [0]` cerca de 60 vezes por segundo no log. O `[0]` é o id do framebuffer: o plano capturado ficou vazio.
- **Causa:** sem HDR, o gamescope passa a usar outro plano, e o Sunshine 2026.914 continua lendo o antigo. Bug upstream: LizardByte/Sunshine#5839 (aberto). Correção parcial no PR #5885, só em pre-release.
- **Solução:** manter o HDR do Game Mode ligado e clarear pelo brilho SDR (acima). Para religar o HDR sem enxergar a tela:

```bash
DISPLAY=:0 xprop -root -f GAMESCOPE_DISPLAY_HDR_ENABLED 32c -set GAMESCOPE_DISPLAY_HDR_ENABLED 1
```

- **Evite** a RPM de pre-release extraída em pasta de usuário: o binário procura `/usr/share/sunshine`, que é somente leitura no Bazzite.

## Sunshine sem tela depois de suspender

- **Diagnóstico:** `No displays were found` após acordar.
- **Solução:** [`config/bazzite/sunshine-resume.service`](../../config/bazzite/sunshine-resume.service) ([07](07-sunshine.md), passo 6).

## Trocar de modo sem mouse

```bash
steamos-session-select gamescope   # vai para o Game Mode
steamos-session-select plasma      # vai para o Modo Desktop
```

Rode com `XDG_RUNTIME_DIR=/run/user/$(id -u)` e `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus` se for pelo SSH. Depois, reinicie o Sunshine.

## Wake-on-LAN do Moonlight não funciona

- **Causa:** o Sunshine informa o MAC como `00:00:…`.
- **Solução:** Alexa ou pacote mágico ([03](03-rede-wol.md)).
