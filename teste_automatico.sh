


screen -dmS SDN_FIREWALL_CONTROLADOR ssh 69.69.69.1 python /root/pox/pox.py misc.l2_learning_mod6

screen -dmS SDN_FIREWALL_MANAGER python /root/sdn_ids/Manager4.py

sleep 10

screen -X -S SDN_FIREWALL_CONTROLADOR quit


