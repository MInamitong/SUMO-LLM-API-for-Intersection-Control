from config import *
import openai
import os
import sys
import win32gui
import win32con
from PyQt5.QtWidgets import QApplication
import openai
import base64
import re
import traci
import sumolib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import dxcam
from PIL import Image
from datetime import datetime
import json

# Use sumo-gui so the simulation GUI is visible
sumo_binary = sumolib.checkBinary('sumo-gui')

class traffic_agent:
    
    def __init__(self):
        # Set up client object
        self.client = openai.OpenAI(
        base_url=api_endpoint,
        api_key=api_key)
        # Initialize conversation history
        self.ctrl_veh_list = ctrl_veh_list
        self.tg_route = 'W_E'
        self.conversation_history = []
        self.hwnd_title = dict()
        self.storage_sites : list = []
        
        self.vehicle_list : dict = {}
        self.ctrl_veh_speed : dict = {}
        self.sgt_ctrl_veh_speed : dict = {}
        self.sgt_phase : dict = {}
        
        self.step : int = 0
        
    def get_all_hwnd(self, hwnd, mouse):
        if win32gui.IsWindow(hwnd) and win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
            self.hwnd_title.update({hwnd: win32gui.GetWindowText(hwnd)})
    
    def get_window_rect(self, hwnd):
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        # rect = win32gui.GetClientRect(hwnd)
        # client_left, client_top, client_right, client_bottom = rect
        return (left, top, right, bottom)
    
    def screen_shot(self):
        win32gui.EnumWindows(self.get_all_hwnd, 0)
        target_hwnd = None
        for hwnd, title in self.hwnd_title.items():
            if target_title in title :
                target_hwnd=hwnd
                print(f'Found target window{title}(HWND:{hwnd})')
                break
        if target_hwnd :
            app = QApplication(sys.argv)
            screen = QApplication.primaryScreen()
            img = screen.grabWindow(target_hwnd).toImage()
            self.storage_site = screenshot_storage.format(step = self.step)  # Update save path
            self.storage_sites.append(self.storage_site)
            img.save(self.storage_site)
            del app
            print('Screenshot saved successfully')
        else :
            print('Target window not found')
    
    def screen_shot_2(self):
        win32gui.EnumWindows(self.get_all_hwnd, 0)
        target_hwnd = None
        for hwnd, title in self.hwnd_title.items():
            if target_title in title :
                target_hwnd=hwnd
                print(f'Found target window{title}(HWND:{hwnd})')
                break
        if not target_hwnd:
            print(f"未找到包括{target_title}的窗口")
            return
        # Bring the target window to the foreground
        win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
        # win32gui.SetForegroundWindow(target_hwnd)
        # Determine the target window coordinates
        left, top, right, bottom = self.get_window_rect(target_hwnd)
        # Create a DXCam camera
        camera = dxcam.create()
        if camera is None:
            print("无法初始化DXCam")
            return
        # Start capturing screenshot
        img = camera.grab(region = (left, top, right, bottom))
        # Update save path
        self.storage_site = screenshot_storage.format(step = self.step)
        self.storage_sites.append(self.storage_site)
        if img is not None:
            Image.fromarray(img).save(self.storage_site)
            print(f"截图已保存至{self.storage_site}")
        else:
            print("截图失败")
        
    def chat_with_gpt(self, base64_images=None):  
        # Update prompt
        self.prompt = template.format(vehicle_speed = self.ctrl_veh_speed)
        user_message = {"role": "user", "content": []}
        user_message["content"].append({"type": "text", "text": self.prompt})
        
        if base64_images:
            if isinstance(base64_images, str):
                base64_images = [base64_images] 
            for img in base64_images:
                user_message["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img}"}
            })
        self.conversation_history.append(user_message)
        user_message = [user_message]
        
        response = self.client.chat.completions.create(
            model=model_id,
            messages=user_message
        )
        reply = response.choices[0].message.content  # extract reply
        print(reply)
        self.conversation_history.append({"role": "assistant", "content": reply})
        return reply
    
    def initialize_ctrl_veh_speed(self):
        for veh_id in self.ctrl_veh_list:
            if veh_id not in self.ctrl_veh_speed:
                self.ctrl_veh_speed[veh_id] = {}
                self.ctrl_veh_speed[veh_id][self.step] = 0
    
    def initialize_sgt_ctrl_veh_speed(self):
        for veh_id in self.ctrl_veh_list:
            if veh_id not in self.sgt_ctrl_veh_speed:
                self.sgt_ctrl_veh_speed[veh_id] = {}
                self.sgt_ctrl_veh_speed[veh_id][self.step] = 0
    
    def get_speed_from_reply(self, reply):
        pattern = r'(\w+):new_speed=(\d+\.?\d*)'
        matches = re.findall(pattern, reply)
        matches_dict = dict(matches)
        new_speed_dict : dict[str, float]= {key: float(value) for key, value in matches_dict.items()}
        #update self.sgt_ctrl_veh_speed
        for veh_id, sgt_speed in new_speed_dict.items():
            self.sgt_ctrl_veh_speed[veh_id][self.step] = sgt_speed
        print(new_speed_dict)
        return new_speed_dict

    def get_phase_from_reply(self, reply):
        pattern = r'phase\s*=\s*(\w+)'
        match = re.search(pattern, reply, re.IGNORECASE)
        if match:
            phase = match.group(1)
            print(f"Phase: {phase}")
            self.sgt_phase[self.step] = phase
            return phase
        else:
            print("未找到phase信息")
            return None
         
    def encode_image(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            print(f"文件未找到: {image_path}")
            return None
        except Exception as e:
            print(f"读取图片文件出错: {e}")
            return None
        
    def encode_images(self, image_paths):
        return [self.encode_image(path) for path in image_paths]
        
    def update_vehicle_data(self, vehicles):
        for veh_id in vehicles:
            # index vehicle speed
            speed = traci.vehicle.getSpeed(veh_id)
            route = traci.vehicle.getRouteID(veh_id)
            # leader = traci.vehicle.getLeader(veh_id)
            # position = traci.vehicle.getPosition(veh_id)
            # if leader:
            #     leader_id, front_gap = leader
            # else:
            #     leader_id = f'Vehicle {veh_id} has no leader'
            #     front_gap = f'Vehicle {veh_id} has no leader'
            if veh_id in self.vehicle_list:
                self.vehicle_list[veh_id]['Speed'][self.step] = speed
                self.vehicle_list[veh_id]['Step'] = self.step
            else: 
                veh_meta_data = {}
                veh_meta_data['Speed'] = {}
                veh_meta_data['Speed'][self.step] = speed
                veh_meta_data['Route'] = route
                veh_meta_data['Step'] = self.step
                self.vehicle_list[veh_id] = veh_meta_data
    
    def get_ctrl_veh_speed(self): 
        
        for veh_id in self.ctrl_veh_list:
            
            enter = veh_id in self.vehicle_list
            if not enter:
                self.ctrl_veh_speed[veh_id][self.step] = 'This car hasn\'t entered the simulation.'
            if enter:
                exit = self.step > self.vehicle_list[veh_id]['Step']
                if not exit:
                    self.ctrl_veh_speed[veh_id][self.step] = self.vehicle_list[veh_id]['Speed'][self.step]
                if exit:
                    self.ctrl_veh_speed[veh_id][self.step] = 'This car has left the simulation.'

    def set_ctrl_veh_speed(self, vehicles):                 
        for veh_id in self.ctrl_veh_list:
            
            # Condition: controlled vehicle has a suggested speed available & is in the simulation
            if (veh_id in list(self.new_speed_dict.keys())) and (veh_id in vehicles):
                # set controlled vehicle speed
                traci.vehicle.setSpeed(veh_id, self.new_speed_dict[veh_id])
    
    def main(self):
        traci.start([sumo_binary, "-c", sumo_cfg_file])

        original_step = None
        
        self.initialize_ctrl_veh_speed()  # initialize controlled vehicle speeds
        self.initialize_sgt_ctrl_veh_speed()  # initialize suggested controlled vehicle speeds
        
        while self.step < simu_len:  # adjust simulation steps
            # perform one simulation step
            traci.simulationStep()
            # originally fetched all vehicle ids; now fetch controlled vehicles only
            vehicles = traci.vehicle.getIDList()
            
            # initialize condition checks
            key_frame = self.step %5 == 0
            has_ctrl_veh = ('Car_3' in vehicles) or ('Car_0' in vehicles)
            
            self.update_vehicle_data(vehicles)
            
            self.get_ctrl_veh_speed()
            
            if has_ctrl_veh:
                self.screen_shot_2()
            
            if has_ctrl_veh and original_step is None:
                original_step = self.step
                print(f'首次有Ctrl Vehicle进入仿真的step为: {original_step}')
            
            # Condition: only when step is a multiple of 5 and controlled vehicles are present do we call the LLM
            if key_frame and has_ctrl_veh:
                print('开始LLM控制')
                if batch_num:
                    gap_satisfied = self.step - original_step >= batch_num
                    print(f'当前仿真步数为{self.step}, 受控车辆出场步数为{original_step}, 是否满足图片间隔条件：{gap_satisfied}')
                    if gap_satisfied:
                        # batch encode images
                        base64_images = self.encode_images(self.storage_sites[-batch_num:])
                        print(f'图片批量编码完成，当前图片数量为{len(base64_images)}')
                        # get LLM reply
                        reply = self.chat_with_gpt(base64_images)

                    else:
                        print(f'不满足图片间隔条件，跳过本次LLM控制')
                        self.step += 1
                        continue  # skip this iteration and proceed to the next simulation step
                
                else:
                    print('默认图片输入为1张')                    
                    # encode single image
                    base64_image = self.encode_image(self.storage_site)
                    print(f'图片编码完成，当前图片数量为1，当前图片地址为{self.storage_site}')
                    # get LLM reply
                    reply = self.chat_with_gpt(base64_image)
                
                # extract speeds from reply
                self.new_speed_dict = self.get_speed_from_reply(reply)
                
                # change vehicle speeds
                self.set_ctrl_veh_speed(vehicles)
                
                # extract simulation phase from reply
                self.ctrl_veh_speed['Phase'] = self.get_phase_from_reply(reply)
                
            
            # update simulation step
            self.step += 1

        # Close the simulation
        traci.close()

    def vehicle_filter(self)-> list[tuple[str, int, int]]:
        tg_vehicle = []
        for veh_id in self.vehicle_list:
            tg_route = self.tg_route
            enter_step = next(iter(self.vehicle_list[veh_id]['Speed'].keys()))
            e_s = min([next(iter(self.vehicle_list[ctrl_veh]['Speed'].keys()))for ctrl_veh in self.ctrl_veh_list])
            
            behind_ctrl_veh = enter_step > e_s
            same_route = self.vehicle_list[veh_id]['Route'] == tg_route
            
            if behind_ctrl_veh and same_route:
                exit_step = list(self.vehicle_list[veh_id]['Speed'].keys())[-1]
                tg_vehicle.append((veh_id, enter_step, exit_step))
        return tg_vehicle
    
    def time_calculation(self):
        tg_vehicle = self.vehicle_filter()
        tg_vehicle = [(veh_id, exit_step - enter_step) for veh_id, enter_step, exit_step in tg_vehicle]
        self.time_record = tg_vehicle

    def save_visualize(self, folder_path, folder_name, mode="有控制"):
        if not self.time_record:
            print("No time records to visualize.")
            return
        time = [t for v, t in self.time_record]
        vehicles = [v for v, t in self.time_record]
        mean_time = np.mean(time)
        plt.figure(figsize=(10, 6))
        plt.plot(time, label=f'Mean Time: {mean_time:.2f} s', marker='o')
        plt.title('Time Record of Vehicles')
        plt.legend()
        plt.grid()
        plt.xlabel('Vehicle ID')
        plt.ylabel('Time (s)')
        plt.xticks(range(len(vehicles)), vehicles, rotation=45)
        # Save image
        img_name = f"{folder_name}-{mode}.png"
        save_path = os.path.join(folder_path, img_name)
        plt.savefig(save_path, bbox_inches='tight')
        print(f"图片已保存至 {save_path}")
        plt.close()

def update_run_count(counter_file='run_count.json'):
    today = datetime.now().strftime('%Y-%m-%d')
    if os.path.exists(counter_file):
        with open(counter_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}
    data[today] = data.get(today, 0) + 1
    with open(counter_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"今天已运行 {data[today]} 次。")
    # Create new folder
    folder_name = f"{today}_{data[today]}"
    folder_path = os.path.join(".", "Output", folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path, folder_name, today, data[today]

if __name__ == '__main__':
    folder_path, folder_name, today, count = update_run_count()
    sumo_agent = traffic_agent()
    sumo_agent.main()
    sumo_agent.time_calculation()
    sumo_agent.save_visualize(folder_path, folder_name, mode="有控制")
    
    #For comparison purpose, run the simulation without LLM control
    # from Test_Runner import simu_runner
    # runner = simu_runner()
    # runner.run_the_simulation()
    # runner.time_calculation()
    # runner.save_visualize(folder_path, folder_name, mode="无控制")

