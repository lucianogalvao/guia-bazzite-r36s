# 03 · Rede, Wake-on-LAN, SSH e Alexa

## Objetivo

Ligar o PC pela rede (ou pela voz) e administrá-lo de outro computador.

## Pré-requisitos

- ErP desativado e "Power On by PCI-E" ativo na BIOS ([01](01-instalacao.md)).
- Acesso ao painel do roteador.

## Passos

1. **IP fixo:** reserve um IP para o MAC do PC no roteador (DHCP reservation).
2. **Wake-on-LAN no Linux.** O nome da conexão varia. Confira com `nmcli connection show`:

```bash
nmcli connection modify "<nome-da-conexão>" 802-3-ethernet.wake-on-lan magic
```

3. **SSH**, para configurar de outro computador:

```bash
sudo systemctl enable --now sshd
ssh-copy-id usuario@IP-DO-PC    # do outro computador
```

4. **Testar o WoL:** desligue o PC e mande o pacote mágico de outro computador na mesma rede. Exemplo em Python, sem instalar nada:

```bash
python3 -c "
import socket; mac='AA:BB:CC:DD:EE:FF'.replace(':','')
p=b'\xff'*6+bytes.fromhex(mac)*16
s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
s.sendto(p,('255.255.255.255',9))"
```

### Opcional: Alexa liga e desliga o PC (TRIGGERcmd)

5. Baixe o agente `.rpm` do TRIGGERcmd e **extraia na pasta pessoal**, sem instalar no sistema (`rpm2cpio pacote.rpm | cpio -idm`).
6. Rode o agente como serviço de usuário. O modelo está em [`config/bazzite/triggercmdagent.service`](../../config/bazzite/triggercmdagent.service). Depois ative o "linger", para ele rodar sem login:

```bash
loginctl enable-linger "$USER"
systemctl --user enable --now triggercmdagent
```

7. Libere só `poweroff` e `reboot` sem senha, para os comandos da Alexa: veja [`config/bazzite/80-triggercmd-power`](../../config/bazzite/80-triggercmd-power). Crie os gatilhos "Desligar" e "Reiniciar" com `sudo -n systemctl poweroff` e `sudo -n systemctl reboot`.
8. No site do TRIGGERcmd: ative o dispositivo Alexa do computador, defina a palavra de voz (ex.: "computador") e **escolha o comando de desligar**. Sem ele, a Alexa não desliga.
9. No app Alexa: ative a skill TRIGGERcmd Smart Home e descubra dispositivos. "Alexa, liga o computador" usa o Wake-on-LAN do próprio Echo.

## Verificação

- O PC liga pelo pacote mágico. No teste, o SSH respondeu em ~20–45 s.
- "Alexa, liga/desliga o computador" funciona.
- `nmcli device show | grep -i speed` mostra 1000.

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| WoL pelo Moonlight não liga o PC | O Sunshine informa o MAC como 00:00:… | Use a Alexa ou o pacote mágico manual |
| Alexa liga, mas não desliga | Falta o comando de desligar no site | Configure o shutdownCommand do computador |
| PC não acorda | ErP ainda ligado | Desative na BIOS |
