from table_util import scale_matrix

def calculate_seat_shares(votes, row_sums, col_sums, scaling):
    (nrows, ncols) = votes.shape
    n_seats = sum(row_sums)
    import numpy as np
    scalar = n_seats/sum(sum(x) for x in votes)
    ref_seat_shares = np.array(scale_matrix(votes, scalar))
    error = 1
    row_constraints = scaling in {"both", "const"}
    col_constraints = scaling in {"both", "party"}
    if ncols > 1 and nrows > 1:
        if row_constraints and col_constraints:
            p_null_seats = set()
            for p in range(ncols):
                if col_sums[p] == 0:
                    p_null_seats.add(p)
                    ref_seat_shares[:, p] *= 0
            while round(error, 7) != 0.0:
                error = 0
                #constituency step
                for c in range(nrows):
                    row_sum = row_sums[c]
                    s = sum(ref_seat_shares[c,:])
                    eta = row_sum/s if s > 0 else 1
                    ref_seat_shares[c, :] *= eta
                    error = max(error, abs(1 - eta))
                if all(i >= 1 for i in ([col_sums[p]/ref_seat_shares.sum(0)[p]
                                         if ref_seat_shares.sum(0)[p] > 0
                                         else 1 for p in range(ncols)])):
                    break
                #party step
                p_at_lim = p_null_seats.copy()
                p_under_lim = set(range(ncols)) - p_at_lim

                def minshare(P):
                    def f(p):
                        return col_sums[p]/ref_seat_shares.sum(axis=0)[p]
                    p = min(P, key=f)
                    return (f(p), p)

                # gammas = np.array([col_sums[p]/ref_seat_shares.sum(axis=0)[p]
                #                   for p in p_under_lim])
                # gamma = np.amin(gammas)
                # gamma = np.min(g[0] for g in gammas)
                # p_gamma = p_under_lim[np.argmin(gammas)]

                (gamma, p_gamma) = minshare(p_under_lim)
                error = max(error, abs(1 - gamma))
                ref_seat_shares *= gamma
                p_at_lim.add(p_gamma)
                p_under_lim.remove(p_gamma)
                nparty_at_lim = len(p_at_lim)
                for i in range(ncols - nparty_at_lim):
                    # gammas = np.array([col_sums[p]/ref_seat_shares.sum(axis=0)[p]
                    #                    for p in p_under_lim])
                    # gamma = np.amin(gammas)
                    # p_gamma = p_under_lim[np.argmin(gammas)]
                    error = max(error, abs(1 - gamma))
                    (gamma, p_gamma) = minshare(p_under_lim)
                    sum_shares = sum([ref_seat_shares.sum(axis=0)[p]*gamma
                                      for p in p_under_lim]) +\
                        sum([ref_seat_shares.sum(axis=0)[p] for p in p_at_lim])
                    if sum_shares > n_seats:
                        break
                    for p in p_under_lim:
                        ref_seat_shares[:,p] *= gamma
                        p_at_lim.add(p_gamma)
                    if p_gamma not in p_under_lim:
                        pass
                    p_under_lim.remove(p_gamma)
                if len(p_under_lim) > 0:
                    gamma = (n_seats - sum([ref_seat_shares.sum(axis=0)[p]
                                            for p in p_at_lim])) \
                        / sum([ref_seat_shares.sum(axis=0)[p] for p in p_under_lim])
                    for p in p_under_lim:
                        ref_seat_shares[:, p] *= gamma
        elif row_constraints:
            for c in range(nrows):
                row_sum = row_sums[c]
                s = sum(ref_seat_shares[c, :])
                eta = row_sum/s if s > 0 else 1
                ref_seat_shares[c, :] *= eta
        elif col_constraints:
            for p in range(ncols):
                col_sum = col_sums[p]
                s = sum(ref_seat_shares[:, p])
                tau = col_sum/s if s > 0 else 1
                ref_seat_shares[:, p] *= tau
    return ref_seat_shares
