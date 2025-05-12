import os
import math
import pandas as pd
from matplotlib import pyplot

def get_gc_content(sequence, verbose=False):
    """Sequence can either be FASTA file location or string"""

    a_count = 0
    t_count = 0
    c_count = 0
    g_count = 0

    def _count_sequence(sequence):
        if not ">" in sequence:
            for character in sequence:
                if character in ["a", "A"]:
                    nonlocal a_count
                    a_count += 1
                elif character in ["t", "T"]:
                    nonlocal t_count
                    t_count += 1
                elif character in ["c", "C"]:
                    nonlocal c_count
                    c_count += 1
                elif character in ["g", "G"]:
                    nonlocal g_count
                    g_count += 1
    if os.path.isfile(sequence):
        filesize = os.path.getsize(sequence)
        bytes_read = 0
        last_update = ""
        line_num = 0
        with open(sequence, 'r') as f:
            # Go to next line
            line = f.readline()
            while line:
                # Stop when you get some weird shit
                if line[0] == ">" or line[0] == "#":
                    print(line)
                    input("Press Enter to continue...")
                # Track progess of reading file
                bytes_read += len(line.encode('utf-8'))
                progress_percent = math.floor(bytes_read * 100 / filesize)
                if progress_percent % 5 == 0:
                    if last_update != progress_percent:
                        last_update = progress_percent
                        print(f"Progress: {progress_percent}%")
                line_num += 1
                # Track GC
                _count_sequence(line)
                line = f.readline()

    else:
        _count_sequence(sequence)
    length = (g_count + c_count + a_count + t_count)
    if length == 0:
        raise ValueError("No bases could be identified in supplied sequence")
    gc_percent = (g_count + c_count) / (g_count + c_count + a_count + t_count)
    if verbose:
        print(f"GC content is {gc_percent*100}%")
    molar_mass = length*(617.41*(1-gc_percent)+618.39*gc_percent)
    return gc_percent, molar_mass

def simulate_pcr(starting_M, cycles=35, annealing_sec=30, length=1000, units=1, gc_product=.5, m_nucleotides=0.0002):
    #  https://doi.org/10.1371/journal.pone.0042063 Based on this paper
    c = starting_M
    k = 3 * pow(10, 5)
    t = annealing_sec
    # https://www.wolframalpha.com/input/?i=%5B%281+minutes+%2F+4000%29+*
    # +avogadro%27s+constant+*+%281mol%2F1000000000nmol%29+*+1nmol%5D+%2F
    # +%5B%2830minutes+%2F+10nmol%29+*+1nmol%5D+*+%5B1%2Favogadro%27s+constant%5D
    # For the phusion math
    c_phusion = units * 8.333 * pow(10, -14)
    # For nucleotide limiting math
    free_nucleotides = m_nucleotides*6.022140857*pow(10, 23)
    nucleotide_usage = length*(.5+abs(gc_product-0.5))
    sim_data = pd.DataFrame(data=None, columns=["Molar_Concentration"])
    sim_data = sim_data.append({"Molar_Concentration": c}, ignore_index=True)
    for _ in range(0, cycles):
        c_previous = c
        if c/(1+k*c*t) > c_phusion:  #  If limit is enzyme
            c = c + c_phusion
        else:  # If limit is template
            c= c * (2 + k * c * t) / (1 + k * c * t)
        if True:  # If limit is nucleotides
            new_molecules = (c-c_previous)*6.022140857*pow(10, 23)
            free_nucleotides -= nucleotide_usage*new_molecules
            if free_nucleotides < 0:
                c = c_previous

        sim_data = sim_data.append({"Molar_Concentration": c}, ignore_index=True)
    fig, ax = pyplot.subplots()
    sim_data.plot(ax=ax)
    ax.set_yscale('log')
    pyplot.ylabel('Mols Product')
    pyplot.xlabel('PCR Cycles')
    pyplot.title('PCR Simulation')
    pyplot.gca().get_legend().remove()
    pyplot.show()
    return c

if __name__ == "__main__":
    file = "C:\\Users\\CRoots\\Downloads\\adp1-genome-nc_005966.fasta"
    _, template_molar_mass = get_gc_content(file, verbose=False)
    print(template_molar_mass)
    sequence = "gtgctactcctgtctgaccccaaccatatccgataaatggtttatgaaatacagcttttaataattgaggccaaatttcaaaccgagaagatcccatagtaagacgatcaaacgtagaatagctatttttttgaaaaaaaattaaattaaatagtaatggaacacaataaactaatgtccaaaatacaatattgaaaaaaataactcttcttaattctatctttttttgaaattttaaaagatataatagagaaatcagaattacacttatccatgcacttctagactgcgtcattacattagcaaaaatcaaacaaaaagataaaatattaaataccatattatttaaactatttttttctcttaaatagcataatagaaataaagttattaaaatcaaagtcgaaaattgatttggttgacccagattagcagtagaacgaccattatatgaggagctaaatagaaaaaaattttgaactatttctattttttgatttatagcaataagaaatgaaatctgaaccacaataataaaaatccaagcaatcttttttactattaggtcatcaccatttaatctttcattaaaacctaaaagaaaactcagaaatagaattactaaaaatgaaattgaaaagaaaaaatcttggaaaaaataaatctcacctacaattaactgaataaaaattatgaatatgacaaataagaaccagtaaaaatttttaggaattagaatttttttataatcaaaggacttcacagttagcaatattagcaaacctaaaactgcaattagctctttatataaagtagaagataaatttgaagtatttggaattataaaagcactaccaaggaaaaatacaccagaaactatcgtgtaatttttgatttttttaaaaatactattcattttttataatttaaagaagaacttataaaagttcttcttttaaagccatatagtactactatcaaccacgacattctgatggtacatattttttatca"
    _, product_molar_mass = get_gc_content(sequence, verbose=False)
    print(product_molar_mass)
    starting_M = 10/1000000000/template_molar_mass
    ending_M = simulate_pcr(starting_M)
    ending_g = ending_M*product_molar_mass
    ending_concentration = ending_g*1000000000/50
    print(f"Simulated resulting PCR concentration: {ending_concentration}ng/ul")
