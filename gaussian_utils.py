# Contains g09 utilities

import os
import re
import subprocess as sb
import time
from statistics import median

import numpy as np
import plotext as plt

DFT_RE = re.compile(r"SCF Done:.*=\s+([^\n]+\d+\.\d+)")
DFT_FREQ = re.compile(r"Frequencies -- (.*)")
FR_RE = re.compile(r"Free Energies=\s+([^\n]+\d+\.\d+)")
EEL_ZPE = re.compile(
    r"Sum of electronic and zero-point Energies=\s+([^\n]+\d+\.\d+)"
)
ZPE_RE = re.compile(r"Zero-point correction=\s+([^\n]+\d+\.\d+)")
ENT_RE = re.compile(r"Enthalpies=\s+([^\n]+\d+\.\d+)")
INP_LINE_RE = re.compile(r"----\n \#(.*\n?.*)-*")
TERM_RE = re.compile(r"Normal termination of Gaussian")
AM1_RE = re.compile(r"")
IRC_RE = re.compile(r"SCF Done:.*=  (-?\d*\.?\d*)")
WRD_LIN = "--------------------------------------------------"
IRC_ERR1 = "This type of calculation cannot be archived."


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
        line = (
            line.replace("#", "")
            .strip()
            .replace("\n", "")
            .replace("  ", " ")
            .replace(WRD_LIN, "")
        )
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

        free = get_free(text)
        result_dict["Free Energy"] = free

    if "freq" in job_line:
        freqs = get_freqs(text)
        result_dict["Frequencies"] = freqs

        zpe = get_zpe(text)
        result_dict["ZPE"] = zpe

        ee_zpe = get_eezpe(text)
        result_dict["EEZPE"] = ee_zpe

    if "irc" in job_line:
        result_dict["IRC"] = gather_irc(text)

    return result_dict


def gather_irc(text):
    irc_ener_str = DFT_RE.findall(text)
    irc_energs = [float(val) for val in irc_ener_str]
    irc_len = len(irc_energs)

    if irc_len % 2 == 0:
        half1 = list(reversed(irc_energs[: (irc_len // 2)]))
        half2 = irc_energs[(irc_len // 2):]
        sort_irc = half1 + half2

    else:
        half = median(range(irc_len))
        print('half: ', half)
        half_v = irc_energs[half]

        half1 = list(reversed(irc_energs[:half+1]))
        half2 = irc_energs[half+1:]

        sort_irc = half1 + half2 

    return sort_irc


def plot_irc(ene_list):

    plt.clf()
    plt.limit_size(False, False)
    plt.plot_size(80, 20)
    plt.canvas_color("default")
    plt.axes_color("default")
    plt.ticks_color("white")
    plt.xlabel("Step")
    plt.ylabel("Energy (Ha)")

    plt.scatter(ene_list)
    plt.title("IRC")

    plt.show()


def print_results(file, result_dict, job_line):
    print_color(f"\n - Results for calculation '{file}':", "green")
    res_avail = result_dict.keys()

    print_color("\n    Calculation Type:", "yellow")
    print("   ", job_line)

    if "Energy" in res_avail:
        print_color("\n    Energetics:", "yellow")
        print(
            f"    Electronic Energy:       {result_dict['Energy']:.6f} Ha   "
            f"  ({ha_to_kcalmol(result_dict['Energy']):.3e} kcal/mol)"
        )
        print(
            f"    ZPE:                      {result_dict['ZPE']} Ha   "
            f"    ({ha_to_kcalmol(result_dict['ZPE']):.3e} kcal/mol)"
        )
        print(
            f"    Electronic Energy + ZPE: {result_dict['EEZPE']} Ha   "
            f"  ({ha_to_kcalmol(result_dict['EEZPE']):.3e} kcal/mol)"
        )
        print(
            f"    Enthalpy:                {result_dict['Enthalpy']} Ha    "
            f" ({ha_to_kcalmol(result_dict['Enthalpy']):.3e} kcal/mol)"
        )

        print(
            f"    Free Energy:             {result_dict['Free Energy']} Ha    "
            f" ({ha_to_kcalmol(result_dict['Free Energy']):.3e} kcal/mol)"
        )

    if "IRC" in res_avail:
        plot_irc(result_dict["IRC"])

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
        # and (IRC_ERR1 not in text):
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
        gauss_ver = os.environ.get("GAUSS_VERSION")

        sb.call(
            [
                f"{gauss_path}/{gauss_ver}",
                f"{cwd}/{fil}",
                f"{cwd}/{output_file}",
            ]
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


def get_eezpe(text):
    ee_zpe = float(EEL_ZPE.findall(text)[-1])
    return ee_zpe


def get_zpe(text):
    zpe = float(ZPE_RE.findall(text)[-1])
    return zpe


def ha_to_kcalmol(value: float):
    return value * 627.503


def get_freqs(text):
    freq_list = []
    freq_line = "".join(DFT_FREQ.findall(text))
    try:
        freq_list = [float(freq) for freq in freq_line.split()]
    except ValueError:
        freq_list = [freq for freq in freq_line.split()]
        for freq in freq_list:
            if "-" in freq and not freq.startswith("-"):
                tmp_freq = freq.split("-")
                tmp_freq[1] = "-" + tmp_freq[1]
                print("tmp_freq: ", tmp_freq)
                freq_ind = freq_list.index(freq)
        new_list = freq_list[:freq_ind] + tmp_freq + freq_list[freq_ind + 1 :]

        freq_list = [float(freq) for freq in new_list]

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
