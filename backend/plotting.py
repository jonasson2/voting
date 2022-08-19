import numpy as np
import matplotlib.pyplot as plt

def plot_sim_party_data(data):
    import numpy as np
    import matplotlib.pyplot as plt
    def get_cumulated_array(data, **kwargs):
        cum = data.clip(**kwargs)
        cum = np.cumsum(cum, axis=0)
        dd = np.zeros(np.shape(data))
        dd[1:] = cum[:-1]
        return dd

    for d in data:
        data = np.array(d)
        data_shape = np.shape(data)
        cumulated_data = get_cumulated_array(data, min=0)
        cumulated_data_neg = get_cumulated_array(data, max=0)

    # Re-merge negative and positive data.
        row_mask = (data < 0)
        cumulated_data[row_mask] = cumulated_data_neg[row_mask]
        data_stack = cumulated_data

        cols = ["g", "y", "b", "c", 'r', 'brown']

        fig = plt.figure()
        ax = plt.subplot(111)

        for i in np.arange(0, data_shape[1]):
            ax.bar(np.arange(data_shape[0]), data[i], bottom=data_stack[i], color=cols[i], )

        plt.savefig('barplot.png')
