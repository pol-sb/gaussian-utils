# Launch g09 scripts

import os
import numpy as np
import subprocess as sb
import time
import re
import pprint as pp
import gaussian_utils as gu

if __name__ == '__main__':

    file_list = [fi for fi in os.listdir() if fi.endswith(".gjf")]

    if not file_list:
        gu.print_color("\nERROR: No input files ('.gjf') found in the current working directory. Aborting.\n", 'red')
        quit()

    cwd = os.getcwd()
    current_time = time.strftime("%H-%M-%S")
    res_fold_name = f"results_{current_time}"
    os.mkdir(res_fold_name)

    gu.run_calculation(file_list, cwd)

    for fil in file_list:
        output_file = f"{fil[:-4]}_res.log"
        termination = gu.check_termination(output_file)

        if termination == "Normal":
            job_line = gu.get_calc_type(output_file)
            res_dict = gu.parse_calc_type(output_file, job_line)
            gu.print_results(output_file, res_dict)
        else:
            gu.print_color(f" - [!] Calculation for file {output_file} Terminated with ERRORS.", "red")

    res_list = [fi for fi in os.listdir() if fi.endswith(".log")]
    chk_list = [fi for fi in os.listdir() if fi.endswith(".chk")]

    for i, val in enumerate(res_list):
        os.replace(res_list[i], f"{res_fold_name}/{res_list[i]}")
        os.replace(chk_list[i], f"{res_fold_name}/{chk_list[i]}")
