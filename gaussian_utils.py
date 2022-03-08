# Contains g09 utilities

import os
import numpy as np
import subprocess as sb
import time
import re
import pprint as pp

DFT_RE = re.compile(r"SCF Done:.*=\s+([^\n]+\d+\.\d+)")
DFT_FREQ = re.compile(r"Frequencies -- (.*)")
FR_RE = re.compile(r"Free Energies=\s+([^\n]+\d+\.\d+)")
ENT_RE = re.compile(r"Enthalpies=\s+([^\n]+\d+\.\d+)")
INP_LINE_RE = re.compile(r"----\n \#(.*)\n-*")
TERM_RE = re.compile(r"Normal termination of Gaussian 09")
AM1_RE = re.compile(r"")


def get_calc_type(file):

    if file.endswith(".gjf"):
        with open(file, "r") as f:
            fil_lines = f.readlines()
            calc_type = [
                line.replace("#", "").strip()
                for line in fil_lines
                if "#" in line
            ]
            return calc_type[0]

    elif file.endswith(".log") or file.endswith(".out"):
        with open(file, "r") as f:
            text = f.read()
        calc_type = re.search(INP_LINE_RE, text)
        # calc_type = INP_LINE_RE.findall(text)
        line = calc_type.group(1)
        line = line.replace("#", "").strip()
        # print(line[0].replace("#", "").strip())

        return line


def get_duration(t1, t2):
    units = ["h", "min", "s"]
    dur_s = t2 - t1

    dur_h = int(dur_s / 3600)
    dur_s -= dur_h * 3600

    dur_min = dur_s / 60
    dur_s -= dur_min * 60

    unit_vals = [dur_h, dur_min, dur_s]

    duration = []
    for i in range(len(units)):
        if unit_vals[i] > 0:
            duration.append(f"{unit_vals[i]:.0f} {units[i]}")

    dur_final = " ".join(duration)
    return dur_final


def parse_calc_type(file: str, job_line: str):
    result_dict = {}

    with open(file, "r") as f:
        text = f.read()

    if "opt" in job_line:
        energ = get_energies(text, job_line)
        result_dict["Energy"] = energ

        enthalp = get_enthalpy(text)
        result_dict["Enthalpy"] = enthalp

        free = get_enthalpy(text)
        result_dict["Free Energy"] = free

    if "freq" in job_line:
        freqs = get_freqs(text)
        result_dict["Frequencies"] = freqs

    return result_dict


def print_results(file, result_dict):
    print_color(f"\n - Results for calculation '{file}':", "green")
    res_avail = result_dict.keys()

    if "Energy" in res_avail:
        print_color("\n    Energetics:", "yellow")
        print(f"    Electronic Energy: {result_dict['Energy']}")
        print(f"    Enthalpy: {result_dict['Enthalpy']}")
        print(f"    Free Energy: {result_dict['Free Energy']} ")

    if "Frequencies" in res_avail:
        print_color("\n    Frequencies:", "yellow")
        freq_arr = np.reshape(
            np.array(result_dict["Frequencies"]),
            (int(len(result_dict["Frequencies"]) / 3), 3),
        )

        np.set_printoptions(formatter={"float": "{0:.1f}".format})

        print(
            "    "
            + str(freq_arr)
            .replace("\n", "\n   ")
            .replace("[", "")
            .replace("]", "")
        )

        n_imagin = np.count_nonzero(np.array(result_dict["Frequencies"]) < 0)

        if not n_imagin:
            print("\n    There are no imaginary frequencies.")
            print_color("    This geometry is a minima.", "blue")

        else:
            print("\n    There are imaginary frequencies.")
            print_color("    This geometry might be a TS.", "blue")

    print_color(f"\n    Calculation '{file}' done.", "green")


def check_termination(output):

    with open(output, "r") as f:
        text = f.read()

    normal_flag = len(TERM_RE.findall(text))

    if normal_flag:
        termination = "Normal"
    else:
        termination = "Error"

    if termination != "Normal":
        print_color(
            f"\n - [!] Calculation '{output}' terminated with ERRORS.", "red"
        )

    return termination


def run_calculation(file_list, cwd):

    for coun, fil in enumerate(file_list):
        curr_time = time.strftime("%H:%M:%S")
        t1 = time.time()
        print_color(
            f"\n[{curr_time}] - Working on '{fil}' - {coun+1}/{len(file_list)}",
            "green",
        )

        job_line = get_calc_type(fil)
        print(job_line)

        output_file = f"{fil[:-4]}_res"

        gauss_path = os.environ.get("GAUSS_EXEDIR")

        sb.call(
            [f"{gauss_path}/g09", f"{cwd}/{fil}", f"{cwd}/{output_file}"]
        )
        t2 = time.time()
        duration = get_duration(t1, t2)
        print(f"Done - Elapsed time {duration}.\n")


def get_energies(text, job_line):

    if "b3lyp" in job_line.lower() or "am1" in job_line.lower():
        energy_value = float(DFT_RE.findall(text)[-1])

    # if 'am1' in job_line.lower():
    #    energy_value = float(DFT_RE.findall(text)[-1])

    return energy_value


def get_enthalpy(text):
    try:
        enth_val = float(ENT_RE.findall(text)[-1])
    except IndexError:
        enth_val = None
    return enth_val


def get_free(text):
    free_val = float(FR_RE.findall(text)[-1])
    return free_val


def get_freqs(text):
    freq_list = []
    freq_line = "".join(DFT_FREQ.findall(text))
    freq_list = [float(freq) for freq in freq_line.split()]

    return freq_list


def print_color(text: str, color: str):
    d_col = {
        "blue": "\033[1;34m",
        "green": "\033[1;32m",
        "red": "\033[1;31m",
        "yellow": "\033[1;33m",
        "normal": "\033[0m",
    }

    print(f"{d_col[color]}{text}{d_col['normal']}")


if __name__ == "__main__":
    print_color(
        "This file is intended to be used as a module, please only use it for"
        " imports",
        "red",
    )
