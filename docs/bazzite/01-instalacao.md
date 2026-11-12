# 01 · Instalação do Bazzite

## Objetivo

Deixar o PC ligando direto no Steam Game Mode, como um console.

## Pré-requisitos

- Pendrive de **16 GB ou mais**. A ISO NVIDIA com Game Mode tem ~9,8 GB.
- Firmware dos controles Xbox atualizado antes de formatar. O app Xbox Accessories só existe no Windows, e qualquer PC com Windows serve.
- Cabo de rede testado: precisa negociar **1000 Mbps**. Com 100 Mbps, a crimpagem provavelmente está ruim.

## Passos

### BIOS (ASUS; `Del` entra, `F8` abre o menu de boot)

1. **XMP:** Ai Tweaker → Ai Overclock Tuner → XMP I. Com i5 de 10ª geração em placa H410/H510, a RAM fica em 2666 MHz mesmo com XMP.
2. **Desativar o ErP.** Sem isso, a placa de rede perde energia com o PC desligado, e o Wake-on-LAN não funciona.
3. **Ativar o "Power On by PCI-E"** em Advanced → APM Configuration. Só aparece depois de desativar o ErP.
4. **Secure Boot:** desative, ou mantenha e registre a chave do Bazzite no primeiro boot (veja o passo 9).
5. **Opcional:** desativar "Wait For 'F1' If Error" (Boot → Boot Configuration), para o boot não parar por falta de teclado.

### Instalação

6. Baixe a ISO em bazzite.gg: Desktop, NVIDIA (RTX), KDE, **Steam Gaming Mode**.
7. Grave o pendrive com Fedora Media Writer ou balenaEtcher.
8. No instalador:
   - **Destino:** marque **só o SSD do sistema**. Os outros discos ficam para depois.
   - **Particionamento:** Automática → Liberar espaço → Excluir tudo. Confira que só o SSD aparece.
   - **Criptografia desmarcada.** Com ela, o PC pede senha a cada boot e o Wake-on-LAN perde o sentido.
   - **Usuário administrador:** em minúsculas, sem espaço nem acento. Sem administrador, `sudo` e `ujust` não funcionam.
9. **Primeiro boot com Secure Boot ligado:** na tela azul "Perform MOK management", escolha Enroll MOK → Continue → Yes, digite a senha `universalblue` e escolha Reboot. Se perder a tela: `ujust enroll-secure-boot-key`.
10. Faça login na Steam. A tela pode ficar preta com um `_` por alguns minutos enquanto a Steam se atualiza.
11. **Atualize tudo logo de cara.** A ISO pode vir bem defasada: a nossa estava um ano atrás, e o Firefox travava ao abrir.

```bash
sudo rpm-ostree upgrade && sudo flatpak update -y
```

12. **Monitor ultrawide com faixas pretas:** Configurações → Tela → desmarque a resolução "Automática" e escolha a nativa.

## Verificação

- O PC liga direto no Game Mode.
- `rpm-ostree status` mostra a imagem nova depois do reboot.

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| Firefox fecha ao abrir | Flatpak antigo da ISO | `sudo flatpak update` |
| Aviso de versão antiga no boot | ISO defasada | `rpm-ostree upgrade` |
| O `!` do Claude Code não aceita senha | Ele não tem terminal interativo | Rode comandos com `sudo` num terminal separado |
