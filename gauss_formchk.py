import gaussian_utils as gu
import os

if __name__ == "__main__":
    cwd = os.getcwd()
    file_list = [chkfil for chkfil in os.listdir() if chkfil.endswith(".chk")]

    if len(file_list) == 0:
        gu.print_color("\nNo '.chk' files found. Aborting.\n", "red")
        quit()

    print("\nConverting the following '.chk' files into '.fchk':")
    print(file_list)

    gu.formchk(filelist=file_list, cwd=cwd)

    print("\nDone.")
