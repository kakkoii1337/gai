from io import BytesIO
import uuid
import os
import json

from gai.lib.common.logging import getLogger
logger = getLogger(__name__)

from gai.tti.client.tti_client import TTIClient
from gai.lib.common.errors import InternalException
from gai.lib.common.image_utils import resize_image
from gai.lib.common.utils import get_app_path
from gai.persona.images.pydantic.AgentImagePydantic import AgentImagePydantic

class SystemImagesMgr:

    def __init__(self, 
        tti_client:TTIClient=None,
        ):
        self.tti = tti_client

    def generate_image_prompt(self, agent_name, personality_traits, image_style, description):
        prompt = f"""
        name: {agent_name};
        personality: {personality_traits};
        style: {image_style};
        pure white background.
        light-colored clothing.
        fusion-look.
        single-person.
        headshot portrait.
        full face-only.
        """
        return prompt

    def generate_negative_prompt(self):
        prompt = f"""
            multiple persons;
            weird eyes;
            goofy face;
            poorly Rendered face;
            poorly drawn face;
            poor facial details;
            poorly drawn hands;
            poorly rendered hands;
            low resolution;
            Images cut out at the top, left, right, bottom;
            bad composition;
            mutated body parts;
            blurry image;
            disfigured;
            oversaturated;
            bad anatomy;
            deformed body features;
            """
        return prompt        

    def generate_image(self, 
        agent_id:str,
        agent_name:str,
        agent_traits: list,
        image_styles: list,
        description: str,
        steps: int=50 
        )->AgentImagePydantic:

        # Generate main copy
        prompt = self.generate_image_prompt(
            agent_name=agent_name, 
            personality_traits=",".join(agent_traits), 
            image_style=",".join(image_styles), 
            description=description)
        negative_prompt = self.generate_negative_prompt()
        image512 = self.tti(prompt=prompt, 
            negative_prompt=negative_prompt, 
            steps=steps,
            output_type = "bytes")

        # Generate resized copies
        agent_image = AgentImagePydantic(Id=agent_id, 
                Image512=image512,
                ImageType='png',
                AgentImagePrompt=self.generate_image_prompt(
                    agent_name=agent_name, 
                    personality_traits=agent_traits, 
                    image_style=image_styles, 
                    description=description),
                AgentImageNegativePrompt=self.generate_negative_prompt(),
                Image256=resize_image(image512, 256,256),
                Image128=resize_image(image512, 128,128),
                Image64=resize_image(image512, 64,64))
        
        return agent_image
    
    # Export image not only saves image but also generate the metadata and thumbnails
    def export_image(self, agent_image:AgentImagePydantic, export_dir:str=None):
        try:
            image_dir = export_dir
            if not image_dir:
                app_path = get_app_path()
                agent_id = agent_image.Id
                image_dir = os.path.join(app_path,"persona",agent_id,"img")            
                if not os.path.exists(image_dir):
                    os.makedirs(image_dir)

            with open(os.path.join(image_dir,"image.json"),"w") as f:
                json.dump({
                    "Id": agent_image.Id,
                    "AgentImagePrompt": agent_image.AgentImagePrompt,
                    "AgentImageNegativePrompt": agent_image.AgentImageNegativePrompt
                },f,indent=4)
            with open(os.path.join(image_dir,"512x512.png"),"wb") as f:
                f.write(BytesIO(agent_image.Image512).getvalue())
            with open(os.path.join(image_dir,"256x256.png"),"wb") as f:
                f.write(BytesIO(agent_image.Image256).getvalue())
            with open(os.path.join(image_dir,"128x128.png"),"wb") as f:
                f.write(BytesIO(agent_image.Image128).getvalue())
            with open(os.path.join(image_dir,"64x64.png"),"wb") as f:
                f.write(BytesIO(agent_image.Image64).getvalue())       
            logger.info(f"system_images_mgr.export_image: Image exported to {image_dir}.")
        except Exception as e:
            id = str(uuid.uuid4())
            logger.error(f"system_images_mgr.export_image: Error exporting image. {e} id={id}")
            raise InternalException(id)

    def get_agent_image(self,agent_id: str, size:str=None) -> bytes:
        try:
            if not size:
                size = "512x512"
            if size not in ["64x64","128x128","256x256","512x512"]:
                raise Exception("Invalid image size")
            app_path = get_app_path()
            persona_img_dir = os.path.join(app_path, "persona", agent_id, "img")
            image_file_path = os.path.join(persona_img_dir, f"{size}.png")  # Assuming PNG by default

            # Check if the image file exists
            if not os.path.isfile(image_file_path):
                raise FileNotFoundError(f"No image found for agent ID: {agent_id}")

            # Read and return the image data
            with open(image_file_path, "rb") as image_file:
                image_data = image_file.read()
            
            return image_data
        except FileNotFoundError as e:
            logger.warning(str(e))
            raise e
        except Exception as e:
            id = str(uuid.uuid4())
            logger.error(f"agent_images_router.get_agent_image: Error getting image from {image_file_path}. {e} id={id}")
            raise InternalException(id)

