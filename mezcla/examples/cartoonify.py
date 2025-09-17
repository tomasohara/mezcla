#! /usr/bin/env python3
#
# Cartoonifies
# - Based on following:
#   https://pypi.org/project/cartoon-diffusion
# - Code prepared with GPT 4.1 (with a bit of trial and error).
#

"""
Convert images to cartoon renditions using cartoon-diffusion

Sample usage:
   {script} --save ~/Downloads/amlo.jpeg

   {script} dylan.png > cartoonified-dylan.png
"""

# Standard modules
from pathlib import Path

# Installed modules
## NOTE: import delayed so --help usage shown sooner (and sans tensorflow junk!)
## OLD: from cartoon_diffusion import CartoonifyDiffusionPipeline

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system

# Constants
TL = debug.TL
SAVE_OPT = "save"
PATH_OPT = "image-path"
OUTPUT_PREFIX = "cartoonified-"

#-------------------------------------------------------------------------------

class CartoonifyHelper:
    """Helper class for converting images to cartoon style"""

    def __init__(self):
        """Initializer: loads the cartoon diffusion pipeline"""
        debug.trace(TL.VERBOSE, f"CartoonifyHelper.__init__(): self={self}")
        # pylint: disable=import-outside-toplevel
        from cartoon_diffusion import CartoonifyDiffusionPipeline
        self.pipeline = CartoonifyDiffusionPipeline.from_pretrained("wizcodes12/image_to_cartoonify")
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def process(self, image_path):
        """Convert image at IMAGE_PATH to cartoon style"""
        cartoon = self.pipeline(image_path)
        return cartoon

    def save_with_prefix(self, cartoon, original_path):
        """Save CARTOON image with prefix based on ORIGINAL_PATH"""
        path = Path(original_path)
        output_path = path.parent / f"{OUTPUT_PREFIX}{path.name}"
        cartoon.save(str(output_path))
        return str(output_path)

#-------------------------------------------------------------------------------

def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Parse command line options
    main_app = Main(
        description=__doc__.format(script=gh.basename(__file__)),
        positional_arguments=[(PATH_OPT, "Path to input image")],
        boolean_options=[(SAVE_OPT, "Save output to file with 'cartoonified-' prefix")],
        manual_input=True
    )
    debug.assertion(main_app.parsed_args)
    
    # Get arguments
    save_to_file = main_app.get_parsed_option(SAVE_OPT)
    image_path = main_app.get_parsed_argument(PATH_OPT)
    
    # Process image
    helper = CartoonifyHelper()
    cartoon = helper.process(image_path)
    
    # Output result
    if save_to_file:
        output_path = helper.save_with_prefix(cartoon, image_path)
        print(f"Created {output_path}")
    else:
        # For stdout output, just save to a temp file and let shell handle piping
        cartoon.save("/dev/stdout")
    
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
