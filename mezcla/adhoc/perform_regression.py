#! /usr/bin/env python3
#
# Runs regression over specifid data file using R.
#
# Notes:
# - Automaes following process
#     data = read.delim("sample-deduped-jobs-title.score.data")
#     fit = lm(RELDIFF ~ REL + NGRAM + POS + CAT + EDIT + FREQ, data=data)
# - R invocation options:
#     --vanilla: Combine --no-save, --no-restore, --no-site-file,  
#                --no-init-file  and --no-environ
#     --verbose:
#
# TODO2:
# - Add regression via pandas and/or sklearn as a sanity check.
#
#-------------------------------------------------------------------------------
# Sample regression output:
#
# R version 2.15.1 (2012-06-22) -- "Roasted Marshmallows"
# ...
# Call:
# lm(formula = RELDIFF ~ REL_SC + NGRAMSC + POS_SC + CAT_SC + EDIT_SC +
#     FREQ_SC, data = data)
#
# Residuals:
#      Min       1Q   Median       3Q      Max
# -0.66196 -0.19160 -0.00842  0.18282  0.79553
#
# Coefficients:
#              Estimate Std. Error t value Pr(>|t|)
# (Intercept) -0.023724   0.008609  -2.756  0.00588 **
# REL_SC       4.052147   0.112756  35.937  < 2e-16 ***
# NGRAMSC     -0.222896   0.025619  -8.700  < 2e-16 ***
# POS_SC       0.106062   0.066014   1.607  0.10818
# CAT_SC       0.161975   0.019235   8.421  < 2e-16 ***
# EDIT_SC      0.274574   0.009212  29.807  < 2e-16 ***
# FREQ_SC     -0.429607   0.019751 -21.751  < 2e-16 ***
# ---
# Signif. codes:  0 '***' 0.001 '**' 0.01 '*' 0.05 '.' 0.1 ' ' 1
#
# Residual standard error: 0.2462 on 5898 degrees of freedom
# Multiple R-squared: 0.4068,     Adjusted R-squared: 0.4062
# F-statistic: 674.1 on 6 and 5898 DF,  p-value: < 2.2e-16
#-------------------------------------------------------------------------------
# TODO:
# - Add option to include diagnostics plot:
#     save_par = par(no.readonly = TRUE)
#     par(mfrow = c(2, 2))
#     plot(fit)
#     par(save_par)
# - Allow for symbolic column specification.
# - Add option to use SciPy-based regression.
#

"""Performs linear regression"""

# Standard modules
import argparse
import re
import sys
import tempfile

# Installed modules
from mezcla import debug
from mezcla import tpo_common as tpo
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.text_utils import extract_string_list

# Constants
TL = debug.TL

# Environment options
TAB_SEPARATED_FEATURES = tpo.getenv_boolean("TAB_SEPARATED_FEATURES", False,
                                            "Separate feature values by tabs")
## OLD: DEFAULT_FEATURE_DELIM = ", " if not TAB_SEPARATED_FEATURES else "\t"
## TODO3: DEFAULT_FEATURE_DELIM = ", *"
DEFAULT_FEATURE_DELIM = "," if not TAB_SEPARATED_FEATURES else "\t"
FEATURE_DELIM = tpo.getenv_text("FEATURE_DELIM", DEFAULT_FEATURE_DELIM, 
                                "Delimiter for output features")
debug.assertion(len(FEATURE_DELIM) == 1)

TEMP_BASE = tpo.getenv_text("TEMP_BASE", tempfile.NamedTemporaryFile().name,
                            "Basename for temporary file(s)")

def main():
    """Entry point for script"""
    tpo.debug_print("main(): sys.argv=%s" % sys.argv, 4)

    # Check command-line arguments
    env_options = tpo.formatted_environment_option_descriptions(indent="  ")
    usage_description = tpo.format("""
Runs regression via R using lm function.
Notes:
- The column numbers are 1-based.
- Install R via apt-get (e.g., "apt-get install --yes --fix-missing r-base").
- The following environment options are available:
  {env}
""", env=env_options)
    parser = argparse.ArgumentParser(description=usage_description, \
                        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--independent-cols", default="",
                        help="Column numbers for independent variables (Xi)")
    parser.add_argument("--dependent-col", type=int, default=1,
                        help="Column number for dependent variable (Y); -1 for last",)
    parser.add_argument("--logit", default=False, action='store_true',
                        help="Perform logistic regression")
    parser.add_argument("--quasi", default=False, action='store_true',
                        help="Use quasi- version of family for glm (e.g., quasibinomial)")
    parser.add_argument("--plot", default=False, action='store_true',
                        help="Output plot (to basename + .png)")
    parser.add_argument("--verbose", default=False, action='store_true',
                        help="Verbose output mode")
    parser.add_argument("--anova", default=False, action='store_true',
                        help="Run anova instead")
    parser.add_argument("--labels", default="",
                        help="Labels for columns--comma separated")
    parser.add_argument("filename", help="Input filename")
    args = vars(parser.parse_args())
    tpo.debug_print("args = %s" % args, 5)
    dependent_col_num = args['dependent_col']
    col_list = args['independent_cols'].replace(",", " ").split()
    independent_col_nums = [tpo.safe_int(c) for c in col_list]
    filename = args['filename']
    produce_plot = args['plot']
    verbose = args['verbose']
    use_logit = args['logit']
    use_quasi = args['quasi']
    use_anova = args['anova']
    labels = args['labels']
    tpo.trace_array(independent_col_nums, 5, "ind")

    # Output stdin to file
    # TODO2: use main to make this automatic
    if filename == "-":
        filename = f"{TEMP_BASE}.in"
        data = f"{labels}\n" if labels else ""
        data += system.read_all_stdin()
        system.write_file(filename, data)
    
    # Extract column names from data file (first line)
    # note: dashses should be converted to underscore for sake of R
    #
    column_names = []
    if labels:
        column_names = extract_string_list(labels)
    else:
        header_line = gh.run("head -1 {f}", f=filename)
        gh.assertion("-" not in header_line)
        ## TODO: header_line = gh.run("head -1 {f}", f=filename).replace("-", "_")
        column_names = header_line.split(FEATURE_DELIM)
    tpo.trace_array(column_names, 5, "column_names")
    #
    if dependent_col_num == -1:
        dependent_col_num = len(column_names)
    gh.assertion(0 < dependent_col_num <= len(column_names))
    #
    # Work out defaults for independent columns
    if not independent_col_nums:
        independent_col_nums = [c for c in range(1, 1 + len(column_names))
                                if c != dependent_col_num]
        tpo.debug_format("independent_col_nums = {nums}", 3,
                         nums=independent_col_nums)

    # Resolve column labels
    def get_column_name(num):
        """Returns symbolic name for column"""
        gh.assertion(num <= len(column_names))
        tpo.trace_array(column_names, 5, "(local) column_names")
        label = column_names[num - 1] if num <= len(column_names) else "???"
        tpo.debug_format("get_column_name({n}) => {l}", 5, n=num, l=label)
        return label
    #
    dependent_label = get_column_name(dependent_col_num)
    independent_labels = [get_column_name(c) for c in independent_col_nums]

    # Create R script for regression
    lm_function = "lm"
    analysis_fn = "summary"
    lm_type = "linear"
    lm_qual = ""
    lm_misc = ""
    if use_logit:
        lm_function = "glm" 
        lm_type = "logistic"
        lm_qual = "generalized "
        family = "binomial"
        if use_quasi:
            family = "quasi" + family
        lm_misc = ", family={f}".format(f=family)
    if use_anova:
        analysis_fn = "anova"
    r_template = """
        # Run {type} regresssion (i.e., {qual}linear model)
        data = read.delim("{f}", sep="{delim}")
        fit = {func}({dep} ~ {ind_spec}, data=data{misc})
        {analysis_fn}(fit)
        """.format(func=lm_function, type=lm_type, qual=lm_qual, misc=lm_misc,
                   f=filename, dep=dependent_label, delim=FEATURE_DELIM,
                   analysis_fn=analysis_fn, ind_spec=(" + ".join(independent_labels)))

    # Optionally produce diagnostic plot
    # TODO: parameterize image type, dimensions, etc.
    if produce_plot:
        image_file = gh.remove_extension(filename, ".data") + ".png"
        r_template += """

            # Produce diagnostics plot
            png(filename="{img_file}", width=1920, height=1080)
            par(mfrow = c(2, 2))
            plot(fit)
            dev.off()
            """.format(img_file=image_file)
        print("Outputting plot to " + image_file)

    # Output script to temp file
    r_file = TEMP_BASE + ".r"
    gh.write_file(r_file, r_template)

    # Run R script in basic mode (i.e., "vanilla" environment)
    options = "--quiet"
    if verbose:
        options += " --verbose"
    output = gh.run("R --vanilla {opt} < {f}", f=r_file, opt=options)
    if use_anova:
        gh.assertion(re.search("Analysis of Variance Table.*F.value", output,
                               re.MULTILINE|re.DOTALL))
    else:
        gh.assertion(re.search("Residuals.*Coefficients.*Intercept", output, \
                               re.MULTILINE|re.DOTALL))
    output = re.sub("^.*Call:", "", output, re.MULTILINE|re.DOTALL)
    print(output)

    return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
