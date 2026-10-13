"""A small multilayer perceptron with hand-written backprop and Adam.

numpy only, so a run is deterministic for a given seed on a given machine and
the whole study runs free on ordinary CPUs. All parameters live in one flat
vector (W and b are views into it) so the optimiser step is a few vectorised
operations. Weight decay is the classic L2 term added to the gradient of every
parameter, as in torch.optim.Adam's weight_decay.
"""

from __future__ import annotations

import numpy as np

SIZES = (32, 128, 128, 4)
BETA1, BETA2, EPS = 0.9, 0.999, 1e-8


def forward_macs(sizes=SIZES) -> int:
    """Multiply-accumulates for one example's forward pass (biases ignored)."""
    return sum(i * o for i, o in zip(sizes[:-1], sizes[1:]))


def n_params(sizes=SIZES) -> int:
    return sum(i * o + o for i, o in zip(sizes[:-1], sizes[1:]))


def softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _views(flat: np.ndarray, sizes):
    Ws, bs, off = [], [], 0
    for i, o in zip(sizes[:-1], sizes[1:]):
        Ws.append(flat[off:off + i * o].reshape(i, o))
        off += i * o
        bs.append(flat[off:off + o])
        off += o
    return Ws, bs


class MLP:
    __slots__ = ("sizes", "theta", "W", "b", "grad", "gW", "gb", "m", "v", "t",
                 "lr", "wd", "init_scale", "_tmp")

    def __init__(self, rng: np.random.Generator, lr: float, wd: float = 0.0,
                 init_scale: float = 1.0, sizes=SIZES):
        self.sizes = tuple(sizes)
        self.lr, self.wd, self.init_scale = float(lr), float(wd), float(init_scale)
        self._alloc(np.zeros(n_params(self.sizes)))
        for l, (i, o) in enumerate(zip(self.sizes[:-1], self.sizes[1:])):
            self.W[l][...] = fresh_weight(rng, i, o, init_scale)
        self.reset_optimizer()

    def _alloc(self, theta: np.ndarray) -> None:
        self.theta = theta
        self.W, self.b = _views(theta, self.sizes)
        self.grad = np.zeros_like(theta)
        self.gW, self.gb = _views(self.grad, self.sizes)
        self._tmp = np.zeros_like(theta)

    def reset_optimizer(self) -> None:
        self.m = np.zeros_like(self.theta)
        self.v = np.zeros_like(self.theta)
        self.t = 0

    def copy(self, with_optimizer: bool = True) -> "MLP":
        c = MLP.__new__(MLP)
        c.sizes, c.lr, c.wd, c.init_scale = self.sizes, self.lr, self.wd, self.init_scale
        c._alloc(self.theta.copy())
        if with_optimizer:
            c.m, c.v, c.t = self.m.copy(), self.v.copy(), self.t
        else:
            c.reset_optimizer()
        return c

    # ---- passes -------------------------------------------------------
    def forward(self, x: np.ndarray):
        """Returns (activations, logits); activations[0] is the input and
        activations[l] for l >= 1 is hidden layer l after ReLU."""
        acts = [x]
        h = x
        last = len(self.W) - 1
        for l in range(last):
            h = h @ self.W[l]
            h += self.b[l]
            np.maximum(h, 0.0, out=h)
            acts.append(h)
        out = h @ self.W[last]
        out += self.b[last]
        return acts, out

    def backward(self, acts, dlogits: np.ndarray, extra=None) -> None:
        """Write gradients into self.grad given dLoss/dlogits; `extra` maps a
        hidden layer index to an additional gradient with respect to that
        layer's activations."""
        d = dlogits
        for l in range(len(self.W) - 1, -1, -1):
            np.matmul(acts[l].T, d, out=self.gW[l])
            np.sum(d, axis=0, out=self.gb[l])
            if l > 0:
                d = d @ self.W[l].T
                if extra is not None and l in extra:
                    d += extra[l]
                d *= acts[l] > 0

    def adam(self) -> None:
        self.t += 1
        lr_t = self.lr * np.sqrt(1.0 - BETA2 ** self.t) / (1.0 - BETA1 ** self.t)
        g, tmp = self.grad, self._tmp
        if self.wd:
            np.multiply(self.theta, self.wd, out=tmp)
            g += tmp
        self.m *= BETA1
        np.multiply(g, 1.0 - BETA1, out=tmp)
        self.m += tmp
        self.v *= BETA2
        np.multiply(g, g, out=tmp)
        tmp *= 1.0 - BETA2
        self.v += tmp
        np.sqrt(self.v, out=tmp)
        tmp += EPS
        np.divide(self.m, tmp, out=tmp)
        tmp *= lr_t
        self.theta -= tmp

    # ---- learning steps ----------------------------------------------
    def train_step(self, x: np.ndarray, y: np.ndarray) -> float:
        """One supervised step; returns the batch accuracy before the update."""
        acts, logits = self.forward(x)
        n = len(y)
        acc = float((logits.argmax(axis=1) == y).mean())
        d = softmax(logits)
        d[np.arange(n), y] -= 1.0
        d /= n
        self.backward(acts, d)
        self.adam()
        return acc

    def teach_step(self, teacher: "MLP", x: np.ndarray) -> None:
        """Match the teacher's hidden activations (MSE, normalised by the
        teacher's mean squared activation) and output distribution (KL)."""
        t_acts, t_logits = teacher.forward(x)
        acts, logits = self.forward(x)
        n = len(x)
        d = (softmax(logits) - softmax(t_logits)) / n
        extra = {}
        for l in range(1, len(acts)):
            target = t_acts[l]
            scale = 1.0 / (float(np.mean(target * target)) + 1e-8)
            extra[l] = 2.0 * scale * (acts[l] - target) / (n * target.shape[1])
        self.backward(acts, d, extra)
        self.adam()

    def accuracy(self, x: np.ndarray, y: np.ndarray) -> float:
        return float((self.forward(x)[1].argmax(axis=1) == y).mean())

    def shrink_perturb(self, rng: np.random.Generator, shrink: float, noise: float) -> None:
        """theta <- shrink * theta + noise * (fresh initial weights); in place."""
        self.theta *= shrink
        for l, w in enumerate(self.W):
            w += noise * fresh_weight(rng, *w.shape, self.init_scale)

    # ---- diagnostics --------------------------------------------------
    def dead_fraction(self, x: np.ndarray) -> float:
        """Share of hidden units that output zero for every input in x."""
        acts, _ = self.forward(x)
        dead = sum(int((a.max(axis=0) <= 0).sum()) for a in acts[1:])
        return dead / sum(self.sizes[1:-1])

    def weight_norm(self) -> float:
        return float(np.sqrt(sum(float((w * w).sum()) for w in self.W)))


def fresh_weight(rng: np.random.Generator, n_in: int, n_out: int, scale: float = 1.0) -> np.ndarray:
    return rng.standard_normal((n_in, n_out)) * (scale * np.sqrt(2.0 / n_in))
