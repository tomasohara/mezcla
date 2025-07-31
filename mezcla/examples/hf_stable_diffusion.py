#! /usr/bin/env python3
#
# Illustrates how to use Stable Diffusion via Hugging Face (HF) diffusers package,
# including gradio-based UI for txt2img and img2img. This also uses the clip_interrogator
# package for img2txt.
#
# Details:
# - via https://huggingface.co/spaces/stabilityai/stable-diffusion
#   also uses https://huggingface.co/CompVis/stable-diffusion-v1-4
#   and https://stackoverflow.com/questions/48273205/accessing-incoming-post-data-in-flask
#
# - This was designed originally for text-to-image (i.e., from prompt to image).
#   However, it has been adapted to support image-to-image as well, which includes an image
#   input along the prompt(s).
#
# - Support is also included for clip interrogation for image-to-text, which is not yet
#   part of the HF diffusers API.
#
# Note:
# - For tips on parameter settings, see
#   https://getimg.ai/guides/interactive-guide-to-stable-diffusion-guidance-scale-parameter
# - For a full-featured interface to Stable Diffusion, see
#   https://github.com/AUTOMATIC1111/stable-diffusion-webui
# - For a stylish Stable Diffusion interface, see
#   https://github.com/comfyanonymous/ComfyUI
#
# TODO2:
# - See why HF keeps downloading model (e.g., make sure cache permanent).
# - Add test cases for flask-based API.
# TODO:
# - Set GRADIO_SERVER_NAME to 0.0.0.0?
#

"""Image generation via HF Stable Diffusion (SD) API"""

# Standard modules
import base64
from io import BytesIO
import json
import time

# Installed modules
import diskcache
from flask import Flask, request
## TODO: see why following needed (i.e., plain PIL import yields intermittent errors)
import PIL.Image
import requests
gr = None

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.text_utils import version_to_number

# Constants/globals
TL = debug.TL
PROMPT = system.getenv_text(
    "PROMPT", "your favorite politician in a tutu",
    description="Positive terms for textual prompt describing image")
NEGATIVE_PROMPT = system.getenv_text(
    "NEGATIVE_PROMPT", "photo realistic",
    description="Negative terms for textual prompt describing image")
GUIDANCE_HELP = "Degree of fidelity to prompt (1-to-30 w/ 7 suggested)--higher for more; aka Classifier Free Guidance (CFG)"
GUIDANCE_SCALE = system.getenv_int(
    "GUIDANCE_SCALE", 7,
    description=GUIDANCE_HELP)
SD_URL_ENV = system.getenv_value(
    "SD_URL", None,
    description="URL for SD TCP/restful server--new via flask or remote")
SD_URL = (SD_URL_ENV if (SD_URL_ENV is not None) and (SD_URL_ENV.strip() not in ["", "-"]) else None)
SD_PORT = system.getenv_int(
    "SD_PORT", 9700,
    description="TCP port for SD server")
SD_DEBUG = system.getenv_int(
    "SD_DEBUG", False,
    description="Run SD server in debug mode")
USE_HF_API = system.getenv_bool(
    "USE_HF_API", not SD_URL,
    description="Use Huggingface API instead of TCP server")
CHECK_UNSAFE = system.getenv_bool(
    "CHECK_UNSAFE", False,
    description="Apply unsafe word list regex filter")
NUM_IMAGES = system.getenv_int(
    "NUM_IMAGES", 1,
    description="Number of images to generated")
BASENAME = system.getenv_text(
    "BASENAME", "sd-app-image",
    description="Basename for saving images")
FULL_PRECISION = system.getenv_bool(
    "FULL_PRECISION", False,
    description="Use full precision GPU computations")
LOW_MEMORY = system.getenv_bool(
    "LOW_MEMORY", (not FULL_PRECISION),
    description="Use low memory computations such as via float16")
DUMMY_RESULT = system.getenv_bool(
    "DUMMY_RESULT", False,
    description="Mock up SD server result")
DISK_CACHE = system.getenv_value(
    "SD_DISK_CACHE", None,
    description="Path to directory with disk cache")
USE_IMG2IMG = system.getenv_bool(
    "USE_IMG2IMG", False,
    description="Use image-to-image instead of text-to-image")
USE_IMG2TXT = system.getenv_bool(
    "USE_IMG2TXT", False,
    description="Use image-to-text instead of image generation")
DENOISING_FACTOR = system.getenv_float(
    "DENOISING_FACTOR", 0.75,
    description="How much of the input image to randomize--higher for more")
HF_SD_MODEL = system.getenv_text(
    "HF_SD_MODEL", "CompVis/stable-diffusion-v1-4",
    description="Hugging Face model for Stable Diffusion")
STREAMLINED_CLIP = system.getenv_bool(
    # note: Doesn't default to LOW_MEMORY, which just uses 16-bit floating point:
    # several settings are changed (see apply_low_vram_defaults in clip_interrogator).
    "STREAMLINED_CLIP", False,
    description="Use streamlined CLIP settings to reduce memory usage")
REGULAR_CLIP = (not STREAMLINED_CLIP)
CAPTION_MODEL = system.getenv_text(
    "CAPTION_MODEL", ("blip-large" if REGULAR_CLIP else "blip-base"),
    description="Caption model to use in CLIP interrogation")
CLIP_MODEL = system.getenv_text(
    "CLIP_MODEL", ("ViT-L-14/openai" if REGULAR_CLIP else "ViT-B-16/openai"),
    # TODO4: see https://arxiv.org/pdf/2010.11929.pdf for ViT-S-NN explanation
    description="Model to use for CLIP interrogation")
#
BATCH_ARG = "batch"
SERVER_ARG = "server"
UI_ARG = "UI"
PORT_ARG = "port"
PROMPT_ARG = "prompt"
NEGATIVE_ARG = "negative"
GUIDANCE_ARG = "guidance"
TXT2IMG_ARG = "txt2img"
IMG2IMG_ARG = "img2img"
IMG2TXT_ARG = "img2txt"
DENOISING_ARG = "denoising-factor"
DUMMY_BASE64_IMAGE = "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPAgMAAABGuH3ZAAAADFBMVEUAAMzMzP////8AAABGA1scAAAAJUlEQVR4nGNgAAFGQUEowRoa6sCABBZowAgsgBEIGUQCRALAPACMHAOQvR4HGwAAAABJRU5ErkJggg=="
DUMMY_IMAGE_FILE = gh.resolve_path("dummy-image.png")
HTTP_OK = 200
# note: RestFUL API keys (via flask)
IMAGES_KEY = "images"
CAPTION_KEY = "caption"

#--------------------------------------------------------------------------------
# Globals
# note: includes support for conditional imports for HF/PyTorch

torch = None
load_dataset = None

word_list = []

sd_instance = None
flask_app = Flask(__name__)


#--------------------------------------------------------------------------------
# Utility function (TODO2: put with others)

def init():
    """Initialize Hugging face for Stable Diffusion"""
    # TODO2: merge with init_stable_diffusion
    debug.trace(4, "in hf_stable_diffusion.init")

    # Load Hugging Face and PyTorch
    global load_dataset, torch
    if USE_HF_API:
        # pylint: disable=import-outside-toplevel, import-error, redefined-outer-name
        from datasets import load_dataset
        import torch

    # Load blacklist for prompt terms
    global word_list
    # pylint: disable=possibly-used-before-assignment
    if CHECK_UNSAFE and load_dataset:
        word_list_dataset = load_dataset("stabilityai/word-list", data_files="list.txt", use_auth_token=True)
        word_list = word_list_dataset["train"]['text']
        debug.trace_expr(5, word_list)
    debug.trace(5, "out hf_stable_diffusion.init")


def show_gpu_usage(level=TL.DETAILED):
    """Show usage for GPU memory, etc.
    TODO: support other types besides NVidia"""
    if USE_HF_API:
        debug.trace(level, "GPU usage")
        debug.trace(level, gh.run("nvidia-smi"))

#-------------------------------------------------------------------------------
# Main Stable Diffusion support

class StableDiffusion:
    """Class providing Stable Diffusion generative AI (e.g., text-to-image)"""

    def __init__(self, use_hf_api=None, server_url=None, server_port=None, low_memory=None):
        ## BAD: debug.trace(4, f"{self.__class__.__name__}.__init__{(use_hf_api, server_url, server_port)}")
        ## TODO2: derive class name from call stack
        class_name = "StableDiffusion"
        debug.trace(4, f"{class_name}.__init__{(use_hf_api, server_url, server_port)}")
        if use_hf_api is None:
            use_hf_api = USE_HF_API
        self.use_hf_api = use_hf_api
        if (server_url is None) and (not self.use_hf_api):
            server_url = SD_URL
        self.server_url = server_url
        if server_port is None:
            server_port = SD_PORT
        if self.server_url and not my_re.search(r"^https?", self.server_url):
            # note: remote flask server (e.g., on GPU server)
            self.server_url = f"http://{self.server_url}"
            debug.trace(4, f"Added http protocol to URL: {self.server_url}")
        if self.server_url:
            if not my_re.search(r":\d+", self.server_url):
                # TODO3: http://base-url/path => http://base-url:port/path
                self.server_url += f":{server_port}"
            elif not server_port:
                system.print_stderr(f"Warning: ignoring port {server_port} as already in URL {self.server_url}")
        elif self.use_hf_api:
            pass
        else:
            debug.trace(4,"Warning: Unexpected condition in {class_name}.__init__: no server_url")
        if low_memory is None:
            low_memory = LOW_MEMORY
        self.low_memory = low_memory
        self.pipe = None
        self.img2txt_engine = None
        self.cache = None
        if DISK_CACHE:
            self.cache = diskcache.Cache(
                DISK_CACHE,                   # path to dir
                disk=diskcache.core.JSONDisk, # avoid serialization issue
                disk_compress_level=0,        # no compression
                cull_limit=0)                 # no automatic pruning
        debug.assertion(bool(self.use_hf_api) != bool(self.server_url))
        show_gpu_usage()
        debug.trace_object(5, self, label=f"{class_name} instance")
    
    def init_pipeline(self, txt2img=None, img2img=None):
        """Initialize Stable Diffusion"""
        debug.trace(4, "init_pipeline()")
        debug.assertion(not (txt2img and img2img))
        ## TODO2: fix lack of support for img2img
        debug.assertion(not img2img)
        # pylint: disable=import-outside-toplevel
        from diffusers import StableDiffusionPipeline
        model_id = HF_SD_MODEL
        device = "cuda"
        # TODO2: automatically use LOW_MEMORY if GPU memory below 8gb
        dtype=(torch.float16 if self.low_memory else None)
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype)
        debug.trace_expr(5, pipe, dtype)
        pipe = pipe.to(device)
        pipe.set_progress_bar_config(disable=True)
        pipe.enable_attention_slicing()
        debug.trace_object(6, pipe)
        show_gpu_usage()
        return pipe

    def init_txt2img(self):
        """Initialize Stable Diffusion text-to-image support (i.e., txt2img)"""
        debug.trace(4, "init_txt2img()")
        return self.init_pipeline(txt2img=True)

    def init_img2img(self):
        """Initialize Stable Diffusion image-to-image support (i.e., img2img)"""
        debug.trace(4, "init_img2img()")
        # pylint: disable=import-outside-toplevel
        from diffusers import StableDiffusionImg2ImgPipeline
        # TODO2: v1-5
        model_id = HF_SD_MODEL
        device = "cuda"
        # TODO2: automatically use LOW_MEMORY if GPU memory below 8gb
        dtype=(torch.float16 if self.low_memory else None)
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(model_id, torch_dtype=dtype)
        debug.trace_expr(5, pipe, dtype)
        pipe = pipe.to(device)
        pipe.set_progress_bar_config(disable=True)
        pipe.enable_attention_slicing()
        debug.trace_object(6, pipe)
        show_gpu_usage()
        return pipe

    def init_clip_interrogation(self):
        """Initialize CLIP interrogation for use with Stable Diffusion"""
        # pylint: disable=import-outside-toplevel
        debug.trace(4, "init_clip_interrogation()")
        from clip_interrogator import Config, Interrogator
        clip_config = Config(caption_model_name=CAPTION_MODEL,
                             clip_model_name=CLIP_MODEL)
        if STREAMLINED_CLIP:
            clip_config.apply_low_vram_defaults()
        self.img2txt_engine = Interrogator(clip_config)

    def infer(self, prompt=None, negative_prompt=None, scale=None, num_images=None,
              skip_img_spec=False, width=None, height=None, skip_cache=False, **kwargs):
        """Generate images using positive PROMPT and NEGATIVE one, along with guidance SCALE,
        and targetting a WIDTHxHEIGHT image.
        Returns list of NUM image specifications in base64 format (e.g., for use in HTML).
        Note: If SKIP_IMG_SPEC specified, result is formatted for HTML IMG tag.
        If SKIP_CACHE, then new results are always generated.
        The KWARGS are used for sub-classing.
        """
        debug.trace_expr(4, prompt, negative_prompt, scale, num_images, skip_img_spec, skip_cache, kwargs, prefix=f"\nin {self.__class__.__name__}.infer:\n\t", delim="\n\t",  suffix="}\n", max_len=1024)
        if num_images is None:
            num_images = NUM_IMAGES
        if scale is None:
            scale = GUIDANCE_SCALE
        for prompt_filter in word_list:
            if my_re.search(rf"\b{prompt_filter}\b", prompt):
                raise RuntimeError("Unsafe content found. Please try again with different prompts.")
    
        images = []
        params = (prompt, negative_prompt, scale, num_images, skip_img_spec, width, height)

        if ((self.cache is not None) and (not skip_cache)):
            images = self.cache.get(params)
        if images and len(images) > 0:
            ## TEST:
            ## debug.trace_fmt(6, "Using cached result for params {p}: ({r})",
            ##                 p=params, r=images)
            debug.trace_fmt(5, "Using cached infer result: ({r})", r=images)
        else:
            images = self.infer_non_cached(*params, **kwargs)
            if self.cache is not None:
                self.cache.set(params, images)
                debug.trace_fmt(6, "Setting cached result (r={r})", r=images)
        return images

    def infer_non_cached(self, prompt=None, negative_prompt=None, scale=None, num_images=None,
                         skip_img_spec=False, width=None, height=None, **kwargs):
        """Non-cached version of infer"""
        params = (prompt, negative_prompt, scale, num_images, skip_img_spec, width, height)
        debug.trace(5, f"{self.__class__.__name__}.infer_non_cached{params}; kwargs={kwargs}")
        images = []
        if self.use_hf_api:
            if DUMMY_RESULT:
                result = [DUMMY_BASE64_IMAGE]
                debug.trace(5, f"early exit infer_non_cached() => {result}")
                return result

            if not self.pipe:
                self.pipe = self.init_pipeline()
            start_time = time.time()
            image_info = self.pipe(prompt, negative_prompt=negative_prompt, guidance_scale=scale,
                                   num_images_per_prompt=num_images, width=width, height=height)
            debug.trace_expr(4, image_info)
            debug.trace_object(5, image_info, "image_info")
            num_generated = 0
            for _i, image in enumerate(image_info.images):
                debug.trace_expr(4, image)
                debug.trace_object(5, image, "image")
                b64_encoding = image
                debug.assertion(isinstance(image, PIL.Image.Image))
                try:
                    num_generated += 1
                    b64_encoding = encode_PIL_image(image)
                    if not skip_img_spec:
                        b64_encoding = (f"data:image/png;base64,{b64_encoding}")
                except:
                    system.print_exception_info("image-to-base64")
                images.append(b64_encoding)
            elapsed = round(time.time() - start_time, 3)
            debug.trace(4, f"{elapsed} seconds to generate {num_images} images")
            debug.assertion(num_generated == num_images)
            show_gpu_usage()
        else:
            debug.assertion(self.server_url)
            url = self.server_url
            payload = {'prompt': prompt, 'negative_prompt': negative_prompt, 'scale': scale,
                       'num_images': num_images}
            images_request = requests.post(url, json=payload, timeout=(5 * 60))
            debug.trace_object(6, images_request)
            debug.trace_expr(5, payload, images_request, images_request.json(), delim="\n")
            for image in images_request.json()[IMAGES_KEY]:
                image_b64 = image
                if not skip_img_spec:
                    image_b64 = (f"data:image/png;base64,{image_b64}")
                images.append(image_b64)
        result = images
        debug.trace_fmt(5, "infer_non_cached() => {r!r}", r=result)
        return result

    def infer_img2img(self, image_b64=None, denoise=None,  prompt=None, negative_prompt=None, scale=None, num_images=None,
                      skip_img_spec=False, skip_cache=False, **kwargs):
        """Generate images from IMAGE_B64 using positive PROMPT and NEGATIVE one, along with guidance SCALE and NUM_IMAGES
        Returns list of NUM image specifications in base64 format (e.g., for use in HTML).
        Note: If SKIP_IMG_SPEC specified, result is formatted for HTML IMG tag.
        If SKIP_CACHE, then new results are always generated.
        The KWARGS are used for sub-classing.
        """
        debug.trace_expr(4, image_b64, denoise, prompt, negative_prompt, scale, num_images, skip_img_spec, skip_cache, kwargs, prefix=f"\nin {self.__class__.__name__}.infer_img2img: {{\n\t", delim="\n\t", suffix="}\n", max_len=1024)
        if num_images is None:
            num_images = NUM_IMAGES
        if scale is None:
            scale = GUIDANCE_SCALE
        if denoise is None:
            denoise = DENOISING_FACTOR
        for prompt_filter in word_list:
            if my_re.search(rf"\b{prompt_filter}\b", prompt):
                raise RuntimeError("Unsafe content found. Please try again with different prompts.")
    
        images = []
        params = (image_b64, denoise, prompt, negative_prompt, scale, num_images, skip_img_spec)

        if ((self.cache is not None) and (not skip_cache)):
            images = self.cache.get(params)
        if images and len(images) > 0:
            ## TEST:
            ## debug.trace_fmt(6, "Using cached result for params {p}: ({r})",
            ##                 p=params, r=images)
            debug.trace_fmt(5, "Using cached infer result: ({r})", r=images)
        else:
            images = self.infer_img2img_non_cached(*params, **kwargs)
            if self.cache is not None:
                self.cache.set(params, images)
                debug.trace_fmt(6, "Setting cached result (r={r})", r=images)
        return images

    def infer_img2img_non_cached(self, image_b64=None, denoise=None, prompt=None, negative_prompt=None, scale=None, num_images=None,
                                 skip_img_spec=False, **kwargs):
        """Non-cached version of infer_img2img"""
        params = (image_b64, denoise, prompt, negative_prompt, scale, num_images, skip_img_spec)
        params_spec = params
        if debug.detailed_debugging():
            params_spec = tuple(map(gh.elide, params))
        debug.trace(5, f"{self.__class__.__name__}.infer_img2img_non_cached{params_spec}; kwargs={kwargs}")
        images = []
        if self.use_hf_api:
            if DUMMY_RESULT:
                result = ["iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPAgMAAABGuH3ZAAAADFBMVEUAAMzMzP////8AAABGA1scAAAAJUlEQVR4nGNgAAFGQUEowRoa6sCABBZowAgsgBEIGUQCRALAPACMHAOQvR4HGwAAAABJRU5ErkJggg=="]
                debug.trace(5, f"early exit infer_img2img_non_cached() => {result}")
                return result

            if not self.pipe:
                self.pipe = self.init_img2img()
            # Get input image
            input_image = create_image(decode_base64_image(image_b64))
            # Generate derived output images(s)
            image_info = self.pipe(image=input_image, strength=denoise, prompt=prompt, negative_prompt=negative_prompt, guidance_scale=scale,
                                   num_images_per_prompt=num_images)
            debug.trace_expr(4, image_info)
            debug.trace_object(5, image_info, "image_info")
            start_time = time.time()
            num_generated = 0
            for _i, image in enumerate(image_info.images):
                debug.trace_expr(4, image)
                debug.trace_object(5, image, "image")
                b64_encoding = image
                debug.assertion(isinstance(image, PIL.Image.Image))
                try:
                    num_generated += 1
                    b64_encoding = encode_PIL_image(image)
                    if not skip_img_spec:
                        b64_encoding = (f"data:image/png;base64,{b64_encoding}")
                except:
                    system.print_exception_info("image-to-base64")
                images.append(b64_encoding)
            elapsed = round(time.time() - start_time, 3)
            debug.trace(4, f"{elapsed} seconds to derive {num_images} images")
            debug.assertion(num_generated == num_images)
            show_gpu_usage()
        else:
            debug.assertion(self.server_url)
            url = self.server_url
            payload = {'image_b64': image_b64, 'strength': denoise, 'prompt': prompt, 'negative_prompt': negative_prompt, 'scale': scale,
                       'num_images': num_images}
            images_request = requests.post(url, json=payload, timeout=(5 * 60))
            debug.trace_object(6, images_request)
            debug.trace_expr(5, payload, images_request, images_request.json(), delim="\n")
            for image in images_request.json()[IMAGES_KEY]:
                image_b64 = image
                if not skip_img_spec:
                    image_b64 = (f"data:image/png;base64,{image_b64}")
                images.append(image_b64)
        result = images
        debug.trace_fmt(5, "infer_img2img_non_cached() => {r!r}", r=result)
        
        return result

    def infer_img2txt(self, image_b64=None, skip_cache=False):
        """Return likely caption text for IMAGE_B64 in base64 encoding
        Note: If SKIP_CACHE, then new results are always generated.
        """
        debug.trace_fmt(4, f"infer_img2txt({gh.elide(image_b64)}, sk={skip_cache})")
        params = (image_b64)
        description = None
        if ((self.cache is not None) and (not skip_cache)):
            description = self.cache.get(params)
        if (description is not None):
            debug.trace_fmt(5, "Using cached infer_img2txt result: ({r!r})", r=description)
        else:
            description = self.infer_img2txt_non_cached(image_b64)
            if self.cache is not None:
                self.cache.set(params, description)
                debug.trace_fmt(6, "Setting cached result (r={r!r})", r=description)
        # Make sure a string
        if (description is None):
            description = ""

        return description
    
    def infer_img2txt_non_cached(self, image_b64=None):
        """Non-cached version of infer_img2txt"""
        image_caption = ""
        if (self.use_hf_api):
            # Get input image and infer likely caption text
            image = create_image(decode_base64_image(image_b64))
            if not self.img2txt_engine:
                self.init_clip_interrogation()
            image_caption = self.img2txt_engine.interrogate(image)
        else:
            debug.assertion(self.server_url)
            url = self.server_url
            payload = {'image_b64': image_b64}
            request_result = requests.post(url, json=payload, timeout=(5 * 60))
            debug.trace_object(6, request_result)
            debug.trace_expr(5, payload, request_result, request_result.json(), delim="\n")
            image_caption = request_result.json()[CAPTION_KEY]
            
        debug.trace_fmt(5, "infer_img2txt_non_cached() => {r!r}", r=image_caption)
        return image_caption
    
#-------------------------------------------------------------------------------
# Middleware

def init_stable_diffusion(use_hf_api=None):
    """Initialize stable diffusion usage, locally if USE_HF_API"""
    debug.trace(4, f"init_stable_diffusion({use_hf_api})")
    init()
    global sd_instance
    sd_instance = StableDiffusion(use_hf_api=use_hf_api)
    debug.trace_expr(5, sd_instance)


@flask_app.route('/', methods=['GET', 'POST'])
def handle_infer():
    """Process request to do inference to generate image from text"""
    # Note: result return via hash with images key
    debug.trace(6, "[flask_app /] handle_infer()")
    # TODO3: request => flask_request
    debug.trace_object(5, request)
    params = request.get_json()
    debug.trace_expr(5, params)
    if not sd_instance:
        init_stable_diffusion()
    images_spec = {IMAGES_KEY: sd_instance.infer(**params)}
    # note: see https://stackoverflow.com/questions/45412228/sending-json-and-status-code-with-a-flask-response
    result = (json.dumps(images_spec), HTTP_OK)
    debug.trace_object(7, result)
    debug.trace_fmt(7, "handle_infer() => {r}", r=result)
    return result


@flask_app.route('/txt2img', methods=['GET', 'POST'])
def handle_infer_txt2img():
    """[Alias] Process request to do inference to generate image from text"""
    debug.trace(6, "[flask_app /] handle_infer_txt2img()")
    return handle_infer()
    

def infer(prompt=None, negative_prompt=None, scale=None, num_images=None, skip_img_spec=None):
    """Wrapper around StableDiffusion.infer()
    Note: intended just for the gradio UI"
    """
    debug.trace(5, f"[sd_instance] infer{(prompt, negative_prompt, scale, skip_img_spec)}")
    if not sd_instance:
        init_stable_diffusion()
    return sd_instance.infer(prompt=prompt, negative_prompt=negative_prompt, scale=scale, num_images=num_images, skip_img_spec=skip_img_spec)


@flask_app.route('/img2img', methods=['GET', 'POST'])
def handle_infer_img2img():
    """Process request to do inference to generate similar image from existing image"""
    # Note: result return via hash with images key
    debug.trace(6, "[flask_app /] handle_infer_img2img()")
    # TODO3: request => flask_request
    debug.trace_object(5, request)
    params = request.get_json()
    debug.trace_expr(5, params)
    if not sd_instance:
        init_stable_diffusion()
    images_spec = {IMAGES_KEY: sd_instance.infer_img2img(**params)}
    # note: see https://stackoverflow.com/questions/45412228/sending-json-and-status-code-with-a-flask-response
    result = (json.dumps(images_spec), HTTP_OK)
    debug.trace_object(7, result)
    debug.trace_fmt(7, "handle_infer_img2img() => {r}", r=result)
    return result


def infer_img2img(image_spec=None, denoise=None,  prompt=None, negative_prompt=None, scale=None, num_images=None, skip_img_spec=None):
    """Wrapper around StableDiffusion.infer_img2img()
    Note: intended just for the gradio UI"
    """
    debug.trace(5, f"[sd_instance] infer_img2img{(gh.elide(image_spec), denoise, prompt, negative_prompt, scale, skip_img_spec)}")
    if isinstance(image_spec, list):
        debug.trace(5, "Warning: using first image in image_spec for infer_img2img")
        image_spec = image_spec[0]
    if ((image_spec is not None) and (not isinstance(image_spec, str))):
        debug.trace_expr(7, image_spec)
        image = (image_spec)
        image_spec = encode_PIL_image(image)
    image_b64 = image_spec        
    if not sd_instance:
        init_stable_diffusion()
    return sd_instance.infer_img2img(image_b64=image_b64, denoise=denoise, prompt=prompt, negative_prompt=negative_prompt, scale=scale, num_images=num_images, skip_img_spec=skip_img_spec)


@flask_app.route('/img2txt', methods=['GET', 'POST'])
def handle_infer_img2txt():
    """Process request to do inference to generate text description of image
    Note: result returned via hash with caption key"""
    ## TODO3: add helper for common flask bookkeeping
    debug.trace(6, "[flask_app /] handle_infer_img2txt()")
    debug.trace_object(5, request)
    params = request.get_json()
    debug.trace_expr(5, params)
    if not sd_instance:
        init_stable_diffusion()
    caption_spec = {CAPTION_KEY: sd_instance.infer_img2txt(**params)}
    result = (json.dumps(caption_spec), HTTP_OK)    
    debug.trace_object(7, result)
    debug.trace_fmt(7, "handle_infer_img2txt() => {r}", r=result)
    return result


def infer_img2txt(image_spec):
    """Wrapper around StableDiffusion.infer_img2txt()
    Note: intended just for the gradio UI"
    """
    debug.trace(5, f"[sd_instance] infer_img2txt({gh.elide(image_spec)})")
    image_b64 = image_spec
    ## TEMP:
    if isinstance(image_b64, PIL.Image.Image):
        image_b64 = encode_PIL_image(image_b64)
    if not sd_instance:
        init_stable_diffusion()
    return sd_instance.infer_img2txt(image_b64)

#--------------------------------------------------------------------------------
# Utility functions

def encode_image_data(image_bytes):
    """Convert IMAGE_BYTES to base64 string"""
    debug.assertion(isinstance(image_bytes, bytes))
    result = base64.b64encode(image_bytes).decode()
    debug.trace(6, f"encode_image_data({gh.elide(image_bytes)}) => {gh.elide(result)}")
    return result


def encode_image_file(filename):
    """Encode image in FILENAME via base64 string"""
    binary_data = system.read_binary_file(filename)
    result = encode_image_data(binary_data)
    debug.trace(6, f"encode_image_file({filename}) => {gh.elide(result)}")
    return result


def encode_PIL_image(image):
    """Convert from PIL image into base64"""
    debug.assertion(isinstance(image, PIL.Image.Image))
    ## BAD: result = encode_image_data(image.tobytes())
    ## note: all sorts of silly issues with PIL!
    bytes_fh = BytesIO()
    image.save(bytes_fh, format="PNG")
    bytes_fh.seek(0)
    result = encode_image_data(bytes_fh.read())
    debug.trace(6, f"encode_PIL_image({gh.elide(image)}) => {gh.elide(result)}")
    return result


def decode_base64_image(image_encoding):
    """Decode IMAGE_ENCODING from base64 returning bytes"""
    # note: "encodes" UTF-8 text of base-64 encoding as bytes object for str, and then decodes into image bytes
    result = base64.decodebytes(image_encoding.encode())
    debug.trace(6, f"decode_base64_image({gh.elide(image_encoding)}) => {gh.elide(result)}")
    return result

def create_image(image_data):           # TODO1: create_PIL_image
    """Create PIL image from IMAGE_DATA bytes"""
    ## TODO4?: create_PIL_image
    result = PIL.Image.open(BytesIO(image_data)).convert("RGB")
    debug.trace(6, f"create_image({gh.elide(image_data)!r}) => {result}")
    return result

def write_image_file(filename, image_spec):
    """Write to FILENAME the base64 data in IMAGE_SPEC"""
    debug.trace(5, f"write_image_file({filename}, {gh.elide(image_spec)})")
    system.write_binary_file(filename, decode_base64_image(image_spec))

#-------------------------------------------------------------------------------
# User interface

def upload_image(upload_control):
    """Upload image data from UPLOAD_CONTROL returning base64 encoded image"""
    debug.trace(4, f"upload_image({upload_control})")
    debug.trace_object(5, upload_control)
    encoded_image = encode_image_file(upload_control.value)
    return encoded_image


def upload_image_file(files):
    """Return path for each of the FILES"""
    debug.trace(4, f"upload_image_file({files})")
    images = [encode_image_file(file.name) for file in files]
    return images


def run_ui(use_img2img=None):
    """Run user interface via gradio serving by default at localhost:7860
    Note: The environment variable GRADIO_SERVER_NAME can be used to serve via 0.0.0.0"""
    ## TEMP: pylint has problem with dynamic classes
    # pylint: disable=no-member
    import gradio as gr                 # pylint: disable=import-outside-toplevel, redefined-outer-name
    is_gradio_4 = version_to_number(gr.__version__) >= 4
    css = """
            .gradio-container {
                font-family: 'IBM Plex Sans', sans-serif;
            }
            .gr-button {
                color: white;
                border-color: black;
                background: black;
            }
            input[type='range'] {
                accent-color: black;
            }
            .dark input[type='range'] {
                accent-color: #dfdfdf;
            }
            .container {
                max-width: 730px;
                margin: auto;
                padding-top: 1.5rem;
            }
            #gallery {
                min-height: 22rem;
                margin-bottom: 15px;
                margin-left: auto;
                margin-right: auto;
                border-bottom-right-radius: .5rem !important;
                border-bottom-left-radius: .5rem !important;
            }
            #gallery>div>.h-full {
                min-height: 20rem;
            }
            .details:hover {
                text-decoration: underline;
            }
            .gr-button {
                white-space: nowrap;
            }
            .gr-button:focus {
                border-color: rgb(147 197 253 / var(--tw-border-opacity));
                outline: none;
                box-shadow: var(--tw-ring-offset-shadow), var(--tw-ring-shadow), var(--tw-shadow, 0 0 #0000);
                --tw-border-opacity: 1;
                --tw-ring-offset-shadow: var(--tw-ring-inset) 0 0 0 var(--tw-ring-offset-width) var(--tw-ring-offset-color);
                --tw-ring-shadow: var(--tw-ring-inset) 0 0 0 calc(3px var(--tw-ring-offset-width)) var(--tw-ring-color);
                --tw-ring-color: rgb(191 219 254 / var(--tw-ring-opacity));
                --tw-ring-opacity: .5;
            }
            #advanced-btn {
                font-size: .7rem !important;
                line-height: 19px;
                margin-top: 12px;
                margin-bottom: 12px;
                padding: 2px 8px;
                border-radius: 14px !important;
            }
            #advanced-options {
                display: none;
                margin-bottom: 20px;
            }
            .footer {
                margin-bottom: 45px;
                margin-top: 35px;
                text-align: center;
                border-bottom: 1px solid #e5e5e5;
            }
            .footer>p {
                font-size: .8rem;
                display: inline-block;
                padding: 0 10px;
                transform: translateY(10px);
                background: white;
            }
            .dark .footer {
                border-color: #303030;
            }
            .dark .footer>p {
                background: #0b0f19;
            }
            .acknowledgments h4{
                margin: 1.25em 0 .25em 0;
                font-weight: bold;
                font-size: 115%;
            }
            .animate-spin {
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                from {
                    transform: rotate(0deg);
                }
                to {
                    transform: rotate(360deg);
                }
            }
            #share-btn-container {
                display: flex; padding-left: 0.5rem !important; padding-right: 0.5rem !important; background-color: #000000; justify-content: center; align-items: center; border-radius: 9999px !important; width: 13rem;
                margin-top: 10px;
                margin-left: auto;
            }
            #share-btn {
                all: initial; color: #ffffff;font-weight: 600; cursor:pointer; font-family: 'IBM Plex Sans', sans-serif; margin-left: 0.5rem !important; padding-top: 0.25rem !important; padding-bottom: 0.25rem !important;right:0;
            }
            #share-btn * {
                all: unset;
            }
            #share-btn-container div:nth-child(-n+2){
                width: auto !important;
                min-height: 0px !important;
            }
            #share-btn-container .wrap {
                display: none !important;
            }
            
            .gr-form{
                flex: 1 1 50%; border-top-right-radius: 0; border-bottom-right-radius: 0;
            }
            #prompt-container{
                gap: 0;
            }
            #prompt-text-input, #negative-prompt-text-input{padding: .45rem 0.625rem}
            #component-16{border-top-width: 1px!important;margin-top: 1em}
            .image_duplication{position: absolute; width: 100px; left: 50px}
    """
    
    block = gr.Blocks(css=css, title="HF Stable Diffusion gradio UI")

    # note: [prompt, negative, guidance]
    txt2img_examples = [
        [
            'A high tech solarpunk utopia in the Amazon rainforest',
            'low quality',
            9, 
        ],
        [
            'A pikachu fine dining with a view to the Eiffel Tower',
            'low quality',
            9, 
        ],
        [
            'A mecha robot in a favela in expressionist style',
            'low quality, 3d, photorealistic',
            9, 
        ],
        [
            'an insect robot preparing a delicious meal',
            'low quality, illustration',
            9,
        ],
    ]
    
    # note: [input_img, denoise_factor, prompt, negative, guidance ]
    img2img_examples = [
        ## TEST: [ DUMMY_BASE64_IMAGE, 0.75, 'A modern Pacman', 'retro', 7, ],
        [ DUMMY_IMAGE_FILE, 0.75, 'A modern Pacman', 'retro', 7, ],
    ]
    

    # Specify CSS styles and SVG data (TODO3: for what?)
    with block:
        gr.HTML(
            """
                <div style="text-align: center; margin: 0 auto;">
                  <div
                    style="
                      display: inline-flex;
                      align-items: center;
                      gap: 0.8rem;
                      font-size: 1.75rem;
                    "
                  >
                    <svg
                      width="0.65em"
                      height="0.65em"
                      viewBox="0 0 115 115"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <rect width="23" height="23" fill="white"></rect>
                      <rect y="69" width="23" height="23" fill="white"></rect>
                      <rect x="23" width="23" height="23" fill="#AEAEAE"></rect>
                      <rect x="23" y="69" width="23" height="23" fill="#AEAEAE"></rect>
                      <rect x="46" width="23" height="23" fill="white"></rect>
                      <rect x="46" y="69" width="23" height="23" fill="white"></rect>
                      <rect x="69" width="23" height="23" fill="black"></rect>
                      <rect x="69" y="69" width="23" height="23" fill="black"></rect>
                      <rect x="92" width="23" height="23" fill="#D9D9D9"></rect>
                      <rect x="92" y="69" width="23" height="23" fill="#AEAEAE"></rect>
                      <rect x="115" y="46" width="23" height="23" fill="white"></rect>
                      <rect x="115" y="115" width="23" height="23" fill="white"></rect>
                      <rect x="115" y="69" width="23" height="23" fill="#D9D9D9"></rect>
                      <rect x="92" y="46" width="23" height="23" fill="#AEAEAE"></rect>
                      <rect x="92" y="115" width="23" height="23" fill="#AEAEAE"></rect>
                      <rect x="92" y="69" width="23" height="23" fill="white"></rect>
                      <rect x="69" y="46" width="23" height="23" fill="white"></rect>
                      <rect x="69" y="115" width="23" height="23" fill="white"></rect>
                      <rect x="69" y="69" width="23" height="23" fill="#D9D9D9"></rect>
                      <rect x="46" y="46" width="23" height="23" fill="black"></rect>
                      <rect x="46" y="115" width="23" height="23" fill="black"></rect>
                      <rect x="46" y="69" width="23" height="23" fill="black"></rect>
                      <rect x="23" y="46" width="23" height="23" fill="#D9D9D9"></rect>
                      <rect x="23" y="115" width="23" height="23" fill="#AEAEAE"></rect>
                      <rect x="23" y="69" width="23" height="23" fill="black"></rect>
                    </svg>
                    <h1 style="font-weight: 900; margin-bottom: 7px;margin-top:5px">
                      Stable Diffusion 2.1 Demo
                    </h1>
                  </div>
                  <p style="margin-bottom: 10px; font-size: 94%; line-height: 23px;">
                    Stable Diffusion 2.1 is the latest text-to-image model from StabilityAI. <a style="text-decoration: underline;" href="https://huggingface.co/spaces/stabilityai/stable-diffusion-1">Access Stable Diffusion 1 Space here</a><br>For faster generation and API
                    access you can try
                    <a
                      href="http://beta.dreamstudio.ai/"
                      style="text-decoration: underline;"
                      target="_blank"
                      >DreamStudio Beta</a
                    >.</a>
                  </p>
                </div>
            """
        )

        # TEMP HACK: make style a no-op under gradio 4
        # NOTE: this is just for sake of testing the API part of the code (i.e., with crippled UI)
        if is_gradio_4:
            def no_op (self, *_args, **_kwargs):
                """No-op[eration] function for gradio 4 breaking changes (without suitable workarounds)"""
                return self
            gr.Textbox.style = no_op
            gr.Button.style = no_op
            gr.Gallery.style = no_op
            gr.Row.style = no_op
        
        # Specify the main form
        # TODO3: be consistent in use of xyz_control
        # NOTE: maldito gradio couldn't care less about backward compatibility; see
        #    https://github.com/gradio-app/gradio/issues/6815 [no attribute 'Box']
        with gr.Group():
            ## TODO3: make sure box behavior honored (e.g., border)
            box = gr.Group if is_gradio_4 else gr.Box
            with box():
                ## TODO: drop 'rounded', border, margin, and other options no longer supported (see log)
                with gr.Row(elem_id="prompt-container").style(mobile_collapse=False, equal_height=True):
                    with gr.Column():
                        prompt_control = gr.Textbox(
                            label="Enter your prompt",
                            show_label=False,
                            max_lines=1,
                            placeholder="Enter your prompt",
                            elem_id="prompt-text-input",
                        ).style(
                            border=(True, False, True, True),
                            rounded=(True, False, False, True),
                            container=False,
                        )
                        negative_control = gr.Textbox(
                            label="Enter your negative prompt",
                            show_label=False,
                            max_lines=1,
                            placeholder="Enter a negative prompt",
                            elem_id="negative-prompt-text-input",
                        ).style(
                            border=(True, False, True, True),
                            rounded=(True, False, False, True),
                            container=False,
                        )
                    btn = gr.Button("Generate image").style(
                        margin=False,
                        rounded=(False, True, True, False),
                        full_width=False,
                    )
    
            gallery = gr.Gallery(
                label="Generated images", show_label=False, elem_id="gallery"
            ).style(grid=[2], height="auto")
    
    
            with gr.Accordion("Advanced settings", open=False):
            #    gr.Markdown("Advanced settings are temporarily unavailable")
            #    samples = gr.Slider(label="Images", minimum=1, maximum=4, value=4, step=1)
            #    steps = gr.Slider(label="Steps", minimum=1, maximum=50, value=45, step=1)
                 guidance_control = gr.Slider(
                    label="Guidance scale", minimum=1, maximum=30, value=GUIDANCE_SCALE, step=0.1
                 )
                 num_control = gr.Slider(
                    label="Number of images", minimum=1, maximum=10, value=2, step=1
                 )
                 img2img_control = gr.Checkbox(label="Use img2img?", value=use_img2img, interactive=True)
                 denoise_control = gr.Slider(label="Denoising factor", minimum=0, maximum=1, value=DENOISING_FACTOR, step=0.05)
                 ## TODO?:
                 input_image_control = gr.Image(label="Input image")  ## TODO?: type='pil'
                 upload_control = gr.UploadButton(label="Upload image", file_types=["image"])
                 interrogate_control = gr.Button(value="CLIP Interrogator")
                 
            #    seed = gr.Slider(
            #        label="Seed",
            #        minimum=0,
            #        maximum=2147483647,
            #        step=1,
            #        randomize=True,
            #    )

            input_controls = [prompt_control, negative_control, guidance_control, num_control]
            output_controls = [gallery]
            infer_fn = infer
            examples = txt2img_examples
            if use_img2img:
                infer_fn = infer_img2img
                input_controls = ([input_image_control, denoise_control] + input_controls)
                examples = img2img_examples
            ex = gr.Examples(examples=examples, fn=infer_fn,
                             inputs=input_controls,
                             outputs=output_controls, cache_examples=False)
            ex.dataset.headers = [""]
            negative_control.submit(infer_fn, inputs=input_controls, outputs=output_controls, postprocess=False)
            prompt_control.submit(infer_fn, inputs=input_controls, outputs=output_controls, postprocess=False)
            btn.click(infer_fn, inputs=input_controls, outputs=output_controls, postprocess=False)
            # TODO1: fix
            upload_control.upload(fn=upload_image_file, inputs=[upload_control], outputs=[input_image_control],
                                  postprocess=False)
            #
            def change_examples():
                """Change examples used in UI if img2img_control checked"""
                debug.trace(4, "change_examples()")
                debug.trace_object(5, img2img_control)
                ex.examples = (img2img_examples if img2img_control.value else txt2img_examples)
            #
            # TODO2: use one listener
            # TODO1: fix
            img2img_control.change(fn=change_examples, inputs=[], outputs=[])
            img2img_control.select(fn=change_examples, inputs=[], outputs=[])
            #
            def use_clip_for_prompt():
                """Run CLIP interrogator over image and send result to prompt field"""
                debug.trace(4, "use_clip_for_prompt()")
                debug.trace_object(5, input_image_control)
                prompt_control.value = infer_img2txt(input_image_control.value)
            #
            # TODO1: fix
            interrogate_control.click(fn=use_clip_for_prompt, inputs=[], outputs=[])
            
            #advanced_button.click(
            #    None,
            #    [],
            #    text,
            #    _js="""
            #    () => {
            #        const options = document.querySelector("body > gradio-app").querySelector("#advanced-options");
            #        options.style.display = ["none", ""].includes(options.style.display) ? "flex" : "none";
            #    }""",
            #)
            gr.HTML(
                """
                    <div class="footer">
                        <p>Model by <a href="https://huggingface.co/stabilityai" style="text-decoration: underline;" target="_blank">StabilityAI</a> - backend running JAX on TPUs due to generous support of <a href="https://sites.research.google/trc/about/" style="text-decoration: underline;" target="_blank">Google TRC program</a> - Gradio Demo by 🤗 Hugging Face
                        </p>
                    </div>
               """
            )
            with gr.Accordion(label="License", open=False):
                gr.HTML(
                    """<div class="acknowledgments">
                        <p><h4>LICENSE</h4>
    The model is licensed with a <a href="https://huggingface.co/stabilityai/stable-diffusion-2/blob/main/LICENSE-MODEL" style="text-decoration: underline;" target="_blank">CreativeML OpenRAIL++</a> license. The authors claim no rights on the outputs you generate, you are free to use them and are accountable for their use which must not go against the provisions set in this license. The license forbids you from sharing any content that violates any laws, produce any harm to a person, disseminate any personal information that would be meant for harm, spread misinformation and target vulnerable groups. For the full list of restrictions please <a href="https://huggingface.co/spaces/CompVis/stable-diffusion-license" target="_blank" style="text-decoration: underline;" target="_blank">read the license</a></p>
                        <p><h4>Biases and content acknowledgment</h4>
    Despite how impressive being able to turn text into image is, beware to the fact that this model may output content that reinforces or exacerbates societal biases, as well as realistic faces, pornography and violence. The model was trained on the <a href="https://laion.ai/blog/laion-5b/" style="text-decoration: underline;" target="_blank">LAION-5B dataset</a>, which scraped non-curated image-text-pairs from the internet (the exception being the removal of illegal content) and is meant for research purposes. You can read more in the <a href="https://huggingface.co/CompVis/stable-diffusion-v1-4" style="text-decoration: underline;" target="_blank">model card</a></p>
                   </div>
                    """
                )

    if not is_gradio_4:
        block.queue(concurrency_count=80, max_size=100).launch(max_threads=150)
    else:
        block.launch()
                
#-------------------------------------------------------------------------------
# Runtime support

def main():
    """Entry point"""

    # Parse command line argument, show usage if --help given
    # TODO? auto_help=False
    main_app = Main(description=__doc__,
                    boolean_options=[(BATCH_ARG, "Use batch mode--no UI"),
                                     (SERVER_ARG, "Run flask server"),
                                     (UI_ARG, "Show user interface"),
                                     (TXT2IMG_ARG, "Run text-to-image--the default"),
                                     (IMG2IMG_ARG, "Run image-to-image"),
                                     (IMG2TXT_ARG, "Run image-to-text: clip interrogator")],
                    text_options=[(PROMPT_ARG, "Positive prompt"),
                                  (NEGATIVE_ARG, "Negative prompt"),
                                  ],
                    int_options=[(GUIDANCE_ARG, GUIDANCE_HELP)],
                    float_options=[(DENOISING_ARG, "Denoising factor for img2img")])
    debug.trace_object(5, main_app)
    debug.assertion(main_app.parsed_args)
    #
    input_image_file = main_app.filename
    BATCH_MODE_DEFAULT = (input_image_file != "-")
    batch_mode = main_app.get_parsed_option(BATCH_ARG, BATCH_MODE_DEFAULT)
    server_mode = main_app.get_parsed_option(SERVER_ARG)
    ui_mode = main_app.get_parsed_option(UI_ARG)
    prompt = main_app.get_parsed_option(PROMPT_ARG, PROMPT)
    negative_prompt = main_app.get_parsed_option(NEGATIVE_ARG, NEGATIVE_PROMPT)
    guidance = main_app.get_parsed_option(GUIDANCE_ARG, GUIDANCE_SCALE)
    use_img2img = main_app.get_parsed_option(IMG2IMG_ARG, USE_IMG2IMG)
    use_img2txt = main_app.get_parsed_option(IMG2TXT_ARG, USE_IMG2TXT)
    use_txt2img = main_app.get_parsed_option(TXT2IMG_ARG, not (use_img2img or use_img2txt))
    denoising_factor = main_app.get_parsed_option(DENOISING_ARG)
    ## TODO?:
    debug.assertion((use_txt2img ^ use_img2img) or use_img2txt)
    # TODO2: BASENAME and NUM_IMAGES (options)
    ## TODO: x_mode = main_app.get_parsed_option(X_ARG)
    debug.assertion(not (batch_mode and server_mode))

    # Invoke UI via HTTP unless in batch or server mode
    show_gpu_usage()
    init_stable_diffusion()
    if batch_mode:
        # Optionally convert input image into base64
        b64_image_encoding = (encode_image_file(input_image_file) if (use_img2img or use_img2txt) else None)

        # Run image generation (or text from image)
        if use_img2txt:
            description = infer_img2txt(b64_image_encoding)
            print(description)
        else:
            images = (infer(prompt, negative_prompt, guidance, skip_img_spec=True) if (not use_img2img)
                      else infer_img2img(b64_image_encoding, denoising_factor, prompt, negative_prompt, guidance, skip_img_spec=True))
            # Save result to disk
            for i, image_encoding in enumerate(images):
                write_image_file(f"{BASENAME}-{i + 1}.png", image_encoding)
            # TODO2: get list of files via infer()
            file_spec = " ".join(gh.get_matching_files(f"{BASENAME}*png"))  
            print(f"See {file_spec} for output image(s).")
    # Start restful server
    elif server_mode:
        debug.assertion(SD_URL)
        debug.assertion(not sd_instance.server_url)
        debug.trace_object(5, flask_app)
        flask_app.run(host=SD_URL, port=SD_PORT, debug=SD_DEBUG)
    # Start UI
    elif ui_mode:
        debug.assertion(main_app.filename == "-")
        run_ui(use_img2img=use_img2img)
    # Otherwise, show command-line options
    else:
        ## TODO3: expose print_usage directly through main_app
        main_app.parser.print_usage()
    show_gpu_usage()


if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_DETAILED)
    main()
