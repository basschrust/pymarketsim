import matplotlib.pyplot as plt

def simple_plot(x: list, y: list, output_file: str) -> None:
    plt.plot(x, y)
    plt.savefig(output_file)

