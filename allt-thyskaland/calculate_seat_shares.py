import numpy as np, math as m

def calculate_seat_shares(votes, row_sums, col_sums, scaling):
    (nrows, ncols) = votes.shape
    total_const_seats = sum(row_sums)
    ref_seat_shares = votes*total_const_seats/votes.sum()
    row_constraints = scaling in {"both", "const"}
    col_constraints = scaling in {"both", "party"}
    if ncols > 1 and nrows > 1:
        iter = 0
        if row_constraints and col_constraints:
            while True:
                iter+=1
                # constituency step
                for c in range(nrows):
                    s = sum(ref_seat_shares[c, :])
                    eta = s/row_sums[c] if row_sums[c] > 0 else 0
                    if eta == 0:
                        ref_seat_shares[c, :] *= 0
                    else:
                        ref_seat_shares[c, :] /= eta
                # party step
                while list(filter(lambda p: sum(ref_seat_shares[:, p]) > col_sums[p],
                                  range(ncols))):
                    H = list(filter(lambda p:
                                    sum(ref_seat_shares[:, p]) >= col_sums[p],
                                    range(ncols)))
                    not_H = list(set(range(ncols)) - set(H))
                    if not_H:
                        s = sum(sum(ref_seat_shares[:, p]) for p in not_H)
                        tau = s/(total_const_seats-sum(col_sums[p] for p in H))
                        for p in not_H:
                            if tau == 0:
                                ref_seat_shares[:, p] *= 0
                            else:
                                ref_seat_shares[:, p] /= tau
                    for p in H:
                        s = sum(ref_seat_shares[:, p])
                        tau = s / col_sums[p] if col_sums[p] > 0 else 0
                        if tau == 0:
                            ref_seat_shares[:, p] *= 0
                        else:
                            ref_seat_shares[:, p] /= tau
                # exit condition
                if m.isclose(sum(abs(sum(ref_seat_shares[c, :])-row_sums[c])
                                 for c in range(nrows)), 0.0, abs_tol=1e-7) and \
                    m.isclose(sum(max(sum(ref_seat_shares[:, p])-col_sums[p], 0.0)
                                  for p in range(ncols)), 0.0, abs_tol=1e-7):
                    break
            print(f'calculate_ref_seat_shares:\titeration count = {iter}')
        elif row_constraints:
            for c in range(nrows):
                row_sum = row_sums[c]
                s = sum(ref_seat_shares[c, :])
                eta = row_sum / s if s > 0 else 1
                ref_seat_shares[c, :] *= eta
        elif col_constraints:
            for p in range(ncols):
                col_sum = col_sums[p]
                s = sum(ref_seat_shares[:, p])
                tau = col_sum / s if s > 0 else 1
                ref_seat_shares[:, p] *= tau
    return ref_seat_shares

def calculate_seat_shares_orig(votes, row_sums, col_sums, scaling):
    (nrows, ncols) = votes.shape
    total_const_seats = sum(row_sums)
    ref_seat_shares = votes*total_const_seats/votes.sum()
    row_constraints = scaling in {"both", "const"}
    col_constraints = scaling in {"both", "party"}
    ref_seat_shares = np.maximum(1e-8, ref_seat_shares)
    if ncols > 1 and nrows > 1:
        iter = 0
        if row_constraints and col_constraints:
            while True:
                if m.isclose(sum(abs(sum(ref_seat_shares[c, :])-row_sums[c])
                                 for c in range(nrows)), 0.0, abs_tol=1e-7) and \
                    m.isclose(sum(max(sum(ref_seat_shares[:, p])-col_sums[p], 0.0)
                                  for p in range(ncols)), 0.0, abs_tol=1e-7):
                    break
                elif iter >= 200:
                    break
                iter +=1
                for c in range(nrows):
                    s = sum(ref_seat_shares[c, :])
                    eta = row_sums[c]/s if s > 0 else 1
                    ref_seat_shares[c, :] *= eta
                for p in range(ncols):
                    col_sum = col_sums[p]
                    s = sum(ref_seat_shares[:, p])
                    tau = col_sums[p]/s if s > 0 else 1
                    ref_seat_shares[:, p] *= tau
    return ref_seat_shares
