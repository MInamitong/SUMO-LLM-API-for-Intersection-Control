# SUMO+LLM API for Intersection Control 
![Cover](images\screenshot.png "Simulation")
This is a simple project based on SUMO and Python. The project simulates the intersection, and utilizes LLM to optimize specific vehicle actions. By controlling these vehicles with LLM, we aim to shorten the average passing time of all vehicles in the controlled direction. It doesn't involve any complicated model training, only the simplest application of API.

## Startup
1. Make sure that you have SUMO installed. I used SUMO-1.19 on my PC. Also, add SUMO path to your system path. If you are using another version of SUMO, check [config.py](#files-8)
   
2. Install the packages in `requirements.txt`.
```
pip install -r requirements.txt
```
3. Fill in the blanks in `Major/config.py`, including api_key, api_endpoint and model_id. The project is developed based on ChatGPT API, therefore if you want to change the model to your favourite LLM, you will need to do some adjustment:
    
    1. In `Major/Simulation.py`, line 28 and 124, that's where you need to modify according to your ideal LLM. 
    2. In `Major/Conversation.py`, line 42, that's another script needs to be modified. 

4. I recommend placing the netedit and sumo-gui shortcut in the project root directory, so that you can check out the SUMO files any time you like.

5. Run `Simulation.py` to start simulation, and screenshots will be saved in `Screenshot/` and vehicle-passing-time will be recorded in `Output/`.
   
## Files
**File Structure:**
```
project/  
├─ .gitignore  
├─ intersection.net.xml     
├─ intersection.rou.xml     
├─ intersection.sumocfg     
├─ README.md        
├─ requirements.txt      
|          
├─generate_vehicles/        
|   ├─ generate_vehicles.py     
|   ├─ routes.xml       
|   └─ traffic_volume.xls     
|             
└─Major/        
    ├─ config.py        
    ├─ Conversation.py      
    ├─ Simulation.py        
    ├─ Test_Runner.py         
    ├─Output        
    └─Screenshot        
```
1. `intersection.net.xml`, `intersection.rou.xml`, and `intersection.sumocfg` are 3 necessary files for SUMO simulation. `intersection.net.xml` records the net configuration, `intersection.rou.xml` records the vehicles' routes, and `intersection.sumocfg` uses the 2 files to start simulation. 
         
2. In directory `generate_vehicles/`, you need to modify the car volume recorded in `traffic_volume.xls`, and run `generate_vehicles.py` to produce a `route.xml`. By changing car volumes, you can control car volumes on each in-and-out routes.

3. `Simulation.py` is the main file, run the script and SUMO GUI will show up. You can start the simulation in SUMO GUI. Once the controlled vehicles enter the simulation, if simulation step is divisible by 5, LLM API is used to control specific vehicles. Speed information and screenshot of the latest step will be input into the model.

    Notice that we have set 2 types of screenshot methods in `Simulation.py`. `Screen_shot` (line 55) grabs the SUMO GUI window, but has some confliction with independent GPU. `Screen_shot_2` (line 75) shows no GPU issues, but your cursor will also appear in the screenshot, and the SUMO GUI window must remain on top.

4. `Screenshot/` storages the screenshorts of simulation.

5. `Output/` storages the results, which will be mean passing time of all vehicles on controlled directions.

6. `Conversation.py` is for raw conversation with LLM, but you can choose whether to include pictures or not. You can use this to test your prompt.

7. `Test_Runner.py` is to run the simulation without any LLM control. It's for pure simulation.

<a id="files-8"></a>

8. `config.py` stores your api_key, api_endpoint and model_id. Enter your tokens, url and chosen model here.

    If you are using another version of SUMO, or another .sumocfg file, don't forget to rewrite `target_title`. This variable designates the window for screenshot during simulation, therefore you need to <u>rewrite "1.19.0" to your SUMO version and "intersection.sumocfg" to your .sumocfg file name</u>.

    Other variables:  
       
    ```
    screenshot_storage: Path to save screenshots
    ctrl_veh_list: Controlled vehicles' IDs, same as those in intersection.rou.xml.
    simu_len: Maximum simulation steps.
    batch_num: Number of photos entered in each conversation.
    ```





