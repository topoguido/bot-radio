from mqqt_broker import Mqtt_listener
import senko_pc
import config
import os
import sys  

def main():
    configs = config.Configs()
    OTA_pc = senko_pc.Senko(
        user = configs._user,
        repo = configs._repo,
        branch = configs._branch, 
        files = configs._files,
        working_dir = configs._working_dir
        )

    if configs.get_status():

        if OTA_pc.update():
            print("Nueva version, instalando y recargando")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            print("soft al dia")

    listener = Mqtt_listener(broker="localhost",client_id="pc-auto")
    listener.start()


if __name__ == "__main__":
    main()



