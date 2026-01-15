from Simulation import *
from config import *

class test_agent(traffic_agent):
    def __init__(self):
        super().__init__()
        self.selected_step = 0
    
    def test(self):
        choice = input('What do you want to do?\n\
                   1: Pick one screenshot and ask the LLM.\n\
                   2: Enter a prompt and ask the LLM.\n\
                   3: Exit.\n')
        if choice == '3':
            exit()
        if choice == '1':
            self.selected_step = int(input('Please enter the existing step number'
                'of the screenshot you want to use:\n'
                '(For more information about available screenshots, '
                'please refer to directory Screenshot ) '))
            image_path = (f"Screenshot/screenshot_{self.selected_step}.jpg")
            base64_image = self.encode_image(image_path)
            Prompt = template.format(vehicle_speed = self.ctrl_veh_speed)    
            self.test_the_gpt(Prompt, base64_image = base64_image)
        elif choice == '2':
            Prompt = input('Please enter your prompt: ')
            base64_image = None
            self.test_the_gpt(Prompt, base64_image=base64_image)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    def test_the_gpt(self, Prompt, base64_image=None):
        
        user_message = {"role": "user", "content": []}
        user_message["content"].append({"type": "text", "text": Prompt})
        if base64_image:
            user_message["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        user_message = [user_message]
        stream = self.client.chat.completions.create(
            model=model_id,
            messages=user_message,
            stream = True
        )
        for chunk in stream:
            if not chunk.choices:
                pass
            else:
                print(chunk.choices[0].delta.content, end = "")


if __name__ == '__main__':
    testor = test_agent()
    testor.main()
    testor.test()
    testor.time_calculation()
    
    