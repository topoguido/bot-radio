from mqqt_broker import Mqtt_listener
import senko_pc
import config
import os
import sys  

def main():
    configs = config.Configs()
    OTA_pc = senko_pc.Senko(
        user = configs.update_user,
        repo = configs.update_repo,
        branch = configs.update_branch, 
        files = configs.update_files,
        working_dir = configs.update_working_dir
        )

    if OTA_pc.update():
        print("Nueva version, instalando y recargando")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print("soft al dia")
        listener = Mqtt_listener(
            broker="localhost",
            client_id="pc-auto",
        )
        listener.start()

if __name__ == "__main__":
    main()



