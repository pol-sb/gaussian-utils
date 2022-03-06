#!/home/tetsuo420/.virtualenvs/modelling/bin/python

# Check the results from g09 calculations

import os
import numpy as np
import subprocess as sb
import time
import gaussian_utils as gu
import re
import pprint as pp

if __name__ == "__main__":

    file_list = [fi for fi in os.listdir() if fi.endswith(".gjf")]
    file_list_check = [fi for fi in os.listdir() if fi.endswith(".log")]

    if not file_list_check:
        gu.print_color(
            "\nERROR: No result files ('.log', '.out') found in the current"
            " working directory. Aborting.\n",
            "red",
        )
        quit()

    if not file_list:
        file_list = [fi for fi in os.listdir() if fi.endswith(".log")]

    errf_list = []

    for fil in file_list:
        if not fil.endswith(".log"):
            output_file = f"{fil[:-4]}_res.log"
        else:
            output_file = fil

        termination = gu.check_termination(output_file)

        if termination == "Normal":
            job_line = gu.get_calc_type(output_file)
            res_dict = gu.parse_calc_type(output_file, job_line)
            gu.print_results(output_file, res_dict)
        else:
            errf_list.append(fil)

    gu.print_color("\nGlobal Results:", "green")
    if errf_list:
        gu.print_color(
            f"\n    [!] - Error on {len(errf_list)}/{len(file_list_check)}"
            " calculations.",
            "red",
        )
        for fil in errf_list:
            print(f"      · {fil}")
        print()
    else:
        gu.print_color("\n     [✓] - No errors found!\n", "yellow")
