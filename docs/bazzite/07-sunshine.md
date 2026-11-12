# 07 · Sunshine (servidor de streaming)

## Objetivo

Transmitir o Game Mode do PC para a TV, codificando pela GPU.

## Pré-requisitos

- Bazzite com Game Mode.
- Um monitor ligado no PC (ou um dummy plug HDMI). Sem tela ativa, não há o que capturar.

## Passos

1. **Instale pelo Homebrew, não pelo Flatpak.** Só a versão do brew captura o Game Mode (captura KMS). Se o brew reclamar de "brew trust" ou "post_install_steps", ele está desatualizado:

```bash
brew update && ujust setup-sunshine enable-brew
```

   No fim, o `ujust` pode dar erro procurando `homebrew.sunshine.service`. É só o nome antigo: o serviço real é `app-dev.lizardbyte.app.Sunshine`.

2. **Confira o serviço:**

```bash
systemctl --user status app-dev.lizardbyte.app.Sunshine
```

3. **Painel web** em `https://IP-DO-PC:47990`: crie o usuário e a senha. Se der "CSRF Protection Error", adicione ao `~/.config/sunshine/sunshine.conf` e reinicie o serviço:

```ini
csrf_allowed_origins = https://IP-DO-PC:47990
```

4. **Encoder pela GPU no Game Mode.** O serviço não herda o display do gamescope, e sem ele o encoder Vulkan falha e o Sunshine cai para `libx264 [software]`. Instale o wrapper e o drop-in:

```bash
install -Dm755 scripts/bazzite/sunshine-start ~/.local/bin/sunshine-start
install -Dm644 config/bazzite/sunshine-20-display.conf \
  ~/.config/systemd/user/app-dev.lizardbyte.app.Sunshine.service.d/20-display.conf
install -Dm644 config/bazzite/sunshine-override.conf \
  ~/.config/systemd/user/app-dev.lizardbyte.app.Sunshine.service.d/override.conf
systemctl --user daemon-reload && systemctl --user restart app-dev.lizardbyte.app.Sunshine
```

   A NVENC não funciona com a captura KMS (`CUDA_ERROR_OPERATING_SYSTEM`). O Vulkan (`h264_vulkan`/`hevc_vulkan`) também codifica na GPU. A 3060 Ti não tem AV1.

5. **Monitor ultrawide + TV 1080p.** O script [`sunshine-res`](../../scripts/bazzite/sunshine-res) põe tudo em 1920×1080 quando o streaming começa. No Game Mode, ele também mantém um vigia, porque a Steam devolve a resolução nativa do monitor a cada jogo aberto. Ajuste as variáveis no topo do script e ligue-o no `sunshine.conf`:

```ini
global_prep_cmd = [{"do":"/home/USUARIO/.local/bin/sunshine-res tv","undo":"/home/USUARIO/.local/bin/sunshine-res parar"}]
```

6. **Retomada após suspensão.** Depois de acordar, o Sunshine perde a tela ("No displays were found"). O serviço [`sunshine-resume.service`](../../config/bazzite/sunshine-resume.service) reinicia o Sunshine 8 s depois de acordar. Troque `USUARIO` no arquivo:

```bash
sudo install -m644 config/bazzite/sunshine-resume.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable sunshine-resume.service
```

## Verificação

```bash
journalctl --user -u app-dev.lizardbyte.app.Sunshine --since -2min -o cat | grep -E "Found .* encoder"
```

Precisa aparecer `h264_vulkan [vulkan]` e `hevc_vulkan [vulkan]`, e não `libx264 [software]`.

## Problemas conhecidos

Veja [10 · Problemas](10-problemas.md): erro 503, "código -1", tela preta com o HDR desligado, imagem escura.
