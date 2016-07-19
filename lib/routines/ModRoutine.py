import colorama
import os
import queue
import subprocess
import threading

from lib.configuration.ModConfiguration import ModConfiguration
from lib.Sample import Sample

from .BaseRoutine import BaseRoutine


class ToolNotFoundException(Exception):
    pass


def check_bowtie():
    """ Checks if bowtie is installed"""
    try:
        subprocess.check_output(["bowtie", "--version"], stderr=subprocess.STDOUT)
        return True
    except FileNotFoundError:
        raise ToolNotFoundException


def check_cutadapt():
    """ Checks if cutadapt is installed"""
    try:
        subprocess.check_output(["cutadapt", "--version"], stderr=subprocess.STDOUT)
        return True
    except FileNotFoundError:
        raise ToolNotFoundException


def check_bedtools():
    """ Checks if bedtools is installed """
    try:
        subprocess.check_output(["bedtools", "--version"], stderr=subprocess.STDOUT)
        return True
    except FileNotFoundError:
        raise ToolNotFoundException


def check_samtools():
    """ Checks if samtools is installed."""
    p = subprocess.Popen("samtools", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()

    if err.startswith(b"\nProgram: samtools (Tools for alignments in the SAM format)\n"):
        return True
    else:
        raise ToolNotFoundException



class ModRoutine(BaseRoutine):
    settings = None
    samples = []
    queue = None

    def get_cli_help(self):
        return "Aligns fastq data to a genom and counts modifications"

    def run(self):
        """ Main loop to run modroutine. """
        self.load_settings()
        self.check_environment()
        self.prepare_input_files()
        self.run_samples()

    def load_settings(self):
        """ Loads configuration """
        self.settings = ModConfiguration("~/QURAlkData/mod_config.ini")

    def check_environment(self):
        """ Controls the environment to make sure that specific programs have been
        installed. """
        print("Check runtime environment...")

        tocheck = [
            ("bowtie", check_bowtie),
            ("cutadapt", check_cutadapt),
            ("bedtools", check_bedtools),
            ("samtools", check_samtools)
        ]

        tool_missing = False

        for tool in tocheck:
            try:
                tool[1]()
                print(" • {} [{}OK{}]".format(tool[0], colorama.Fore.GREEN, colorama.Fore.RESET))
            except ToolNotFoundException:
                print(" • {} [{}MISSING{}]".format(tool[0], colorama.Fore.RED, colorama.Fore.RESET))
                tool_missing = True

        if tool_missing:
            print("Not all tools have been found. The run has been aborted.")
            exit()

    def prepare_input_files(self):
        """ Prepares the input files: gzipped files are wanted. If non-compressed fasta files are found, they will be
        compressed."""
        files = []
        samples = []
        input_directory = self.settings.get("InputDirectory")

        for filename in os.listdir(input_directory):
            # Skip if hidden
            if filename.startswith("."):
                continue

            # Get the first part of the filename
            sample_name = filename.split(".")[0]

            if sample_name in samples:
                print("[Warning] Sample " + sample_name + " has already been found. " + filename + " has been ignored.")
                continue

            if filename.endswith(".fastq"):
                # non-gzip files must be packed first
                target_file = os.path.join(*[input_directory, filename])
                try:
                    subprocess.check_output("gzip -f " + target_file, shell=True)
                except:
                    print("[Error] It was not possible to pack " + filename)
                    raise Exception("Aborted")

                samples.append(sample_name)
                files.append(os.path.join(*[input_directory, filename + ".gz"]))
            elif filename.endswith(".fastq.gz"):
                samples.append(sample_name)
                files.append(os.path.join(*[input_directory, filename]))

        self.samples = samples

    def run_samples(self):
        """ Runs the calculation pipeline on every sample found. """
        # Abort if number of samples is 0.
        if len(self.samples) == 0:
            raise Exception("\Found no .fastq(.gz) files to work with.")

        # Queue creation
        self.queue = queue.Queue()

        # Show an overview over found input files for giving a feedback to the user
        print("\nFound %i .fastq.gz files to work with:" % (len(self.samples),))

        for sampleFile in self.samples:
            print(" • %s" % (os.path.basename(sampleFile, )))

        print("")

        # Now split the task into smaller ones for parallelization
        try:
            # Boot threads
            for i in range(0, self.settings.get("MaxPythonThreads")):
                t = threading.Thread(target=self.run_threads)
                t.daemon = True
                t.start()

            # Add samples to queue
            for sampleFile in self.samples:
                self.queue.put(sampleFile)

            # Blocks until all tasks are done
            self.queue.join()

            # Report success
            print("\nTasks are done.")
        except Exception as e:
            raise Exception("Unknown exception raised: " + str(e))

    def run_threads(self):
        """ Gets called by threads. Fetches a sample, runs the calculation processes and reports
        to the queue that it's done. """
        while True:
            samplename = self.queue.get()
            sample = Sample(samplename, self.settings)
            sample.run()

            self.queue.task_done()
