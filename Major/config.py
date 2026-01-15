import os
import sys
import json

# API key configuration
api_key : str = ""
# Endpoint URL configuration
api_endpoint : str = ""
# Model type
model_id : str = ""


# SUMO configuration file path
sumo_cfg_file : str =r"..\intersection.sumocfg"
# Window title for screenshot capture
target_title : str = 'intersection.sumocfg - SUMO 1.19.0'

# Add SUMO libraries to Python module search path
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
    
    
# Screenshot storage location
screenshot_storage="Screenshot/screenshot_{step}.jpg"
# Controlled vehicle IDs
ctrl_veh_list = ['Car_0', 'Car_1','Car_2']
# Simulation duration (in steps)
simu_len = 500
# Number of input images
batch_num = 3


# Model prompt/instructions
template = (
    "Role: Traffic control expert for unsignalized intersections.\n"
    "## Goal:  \n"
    "Shorten crossing time by controlling red vehicles' speeds and phases.\n\n"
    
    "## Input:  \n"
    "1. **Real-time vehicle speeds (Red=Controlled vehicles)**:  \n"
    "   {vehicle_speed}  \n"
    "   - Format: {{'phase': last_phase, 'vehicle_id': {{time_step: speed (m/s)}}}}\n"
    "   - Vehicle positions:  \n"
    "     • Eastbound lanes (top→bottom): Car_2 (1st), Car_1 (2nd), Car_0 (3rd)  \n"
    "2. **SUMO simulation images**:  \n"
    "   - Show congestion status & vehicle distribution  \n"
    "   - Scale reference in bottom-left corner  \n\n"
    
    "## Phase Definition:  \n"
    "1. **Phase1**: Congestion buildup (blue vehicles slowing)  \n"
    "2. **Phase2**: Red vehicles approaching stop line  \n"
    "3. **Phase3**: Red vehicles stop at line  \n"
    "4. **Phase4**: Wait for intersection clearance  \n"
    "5. **Phase5**: Cross intersection \n\n"
    
    "## Requirements:  \n"
    "1. **Phase analysis**:  \n"
    "   - Determine current phase using:  \n"
    "     • Speed trend from input data  \n"
    "     • Congestion level in images  \n"
    "   - Only advance phases (1→2→3→4→5)  \n"
    "2. **Speed control**:  \n"
    "   - Desired speed=20m/s  \n"
    "   - Apply **car-following model** (e.g., IDM/Gipps)  \n"
    "   - Optimize for minimum crossing time  \n"
    "   - Ensure safe distances (use image scale)  \n\n"
    
    "## Output Format:  \n"
    "phase=PhaseX  \n"
    "model=ModelName  \n"
    "Car_0:new_speed=A  \n"
    "Car_1:new_speed=B  \n"
    "Car_2:new_speed=C  \n"
    "No other output"
)
# Calculate according to certain logic, similar to car-following model
