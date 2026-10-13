# Related work (working list)

Each entry says why it matters for Study 1. Check every citation against the
published version before submission. Entries marked † are recalled from
memory and not yet checked against the paper itself.

## Loss of plasticity: why an immortal learner may stall

- **Dohare, S., Hernandez-Garcia, J. F., Lan, Q., Rahman, P., Mahmood, A. R., & Sutton, R. S. (2024).** Loss of plasticity in deep continual learning. *Nature*, 632, 768–774.
  - Standard deep networks gradually lose the ability to learn in continual
    settings.
  - "Continual backprop" (reinitialising low-utility units) maintains
    plasticity.
  - This is the central mechanism by which reproduction could beat
    immortality.
- **Lyle, C., Zheng, Z., Nikishin, E., Pires, B. A., Pascanu, R., & Dabney, W. (2023).** Understanding plasticity in neural networks. *ICML*.
  - Plasticity loss linked to the loss-landscape curvature.
  - Layer normalisation and related interventions mitigate it.
- **Ash, J. T., & Adams, R. P. (2020).** On warm-starting neural network training. *NeurIPS*.
  - Warm-started networks generalise worse than fresh ones.
  - Proposes shrink-and-perturb, which is our RESET arm.
- **Nikishin, E., Schwarzer, M., D'Oro, P., Bacon, P.-L., & Courville, A. (2022).** The primacy bias in deep reinforcement learning. *ICML*.
  - Early experience overfits the agent.
  - Periodic resets of the last layers help.
- **Sokar, G., Agarwal, R., Castro, P. S., & Evci, U. (2023).** The dormant neuron phenomenon in deep reinforcement learning. *ICML*.
  - Units go inactive during training. Our "dead units" diagnostic.
- **Kumar, S., Marklund, H., & Van Roy, B. (2023).** Maintaining plasticity in continual learning via regenerative regularization. *arXiv:2308.11958*.†
- **Elsayed, M., & Mahmood, A. R. (2024).** Addressing loss of plasticity and catastrophic forgetting in continual learning. *ICLR*.†

## Passing knowledge to a fresh network: why teaching might help

- **Furlanello, T., Lipton, Z. C., Tschannen, M., Itti, L., & Anandkumar, A. (2018).** Born-again neural networks. *ICML*.
  - A student identical to its teacher, trained by distillation,
    outperforms the teacher.
- **Igl, M., Farquhar, G., Luketina, J., Boehmer, W., & Whiteson, S. (2021).** Transient non-stationarity and generalisation in deep reinforcement learning. *ICLR*.
  - ITER periodically distils the agent into a fresh network and improves
    generalisation.
  - The closest precedent to our TEACH arm.
- **Hinton, G., Vinyals, O., & Dean, J. (2015).** Distilling the knowledge in a neural network. *arXiv:1503.02531*.
- **Romero, A., Ballas, N., Kahou, S. E., Chassang, A., Gatta, C., & Bengio, Y. (2015).** FitNets: Hints for thin deep nets. *ICLR*.
  - Matching intermediate representations; our TEACH matches the last
    hidden layer.
- **Zhou, H., Vani, A., Larochelle, H., & Courville, A. (2022).** Fortuitous forgetting in connectionist networks. *ICLR*.
  - Forget-and-relearn cycles improve generalisation.
- **Taha, A., Shrivastava, A., & Davis, L. S. (2021).** Knowledge evolution in neural networks. *CVPR*.
  - Generations of partial re-initialisation improve small-data learning.
- **Ren, Y., Guo, S., Labeau, M., Cohen, S. B., & Kirby, S. (2020).** Compositional languages emerge in a neural iterated learning model. *ICLR*.
- **Kirby, S., Griffiths, T. L., & Smith, K. (2014).** Iterated learning and the evolution of language. *Current Opinion in Neurobiology*, 28, 108–114.
  - Transmission through a bottleneck shapes what is learned.

## Populations, selection and the Baldwin effect

- **Jaderberg, M., et al. (2017).** Population based training of neural networks. *arXiv:1711.09846*.
  - Exploit (copy weights) and explore (perturb hyperparameters). Our CLONE
    arm.
- **Hinton, G. E., & Nowlan, S. J. (1987).** How learning can guide evolution. *Complex Systems*, 1, 495–502.
  - The Baldwin effect: inheriting the ability to learn, not what was
    learned. Our GENES arm.
- **Real, E., Liang, C., So, D. R., & Le, Q. V. (2020).** AutoML-Zero: Evolving machine learning algorithms from scratch. *ICML*.
- **Zhang, J., Hu, S., Lu, C., Lange, R., & Clune, J. (2025).** Darwin Gödel Machine: Open-ended evolution of self-improving agents. *arXiv:2505.22954*.
  - Evolves agent code around frozen foundation models.
- **Akiba, T., Shing, M., Tang, Y., Sun, Q., & Ha, D. (2025).** Evolutionary optimization of model merging recipes. *Nature Machine Intelligence*.†
- **Wang, R., Lehman, J., Clune, J., & Stanley, K. O. (2019).** Paired open-ended trailblazer (POET). *arXiv:1901.01753*.

## Why the staircase world: learnability of parities

- **Abbe, E., Boix-Adserà, E., & Misiakiewicz, T. (2022).** The merged-staircase property: a necessary and nearly sufficient condition for SGD learning of sparse functions on two-layer neural networks. *COLT*.
  - Functions whose monomials can be reached one variable at a time are
    learnable efficiently. Isolated high-degree parities are not.
  - This is why accumulated knowledge matters in our world.
- **Barak, B., Edelman, B. L., Goel, S., Kakade, S., Malach, E., & Zhang, C. (2022).** Hidden progress in deep learning: SGD learns parities near the computational limit. *NeurIPS*.

## Forgetting

- **Kirkpatrick, J., et al. (2017).** Overcoming catastrophic forgetting in neural networks. *PNAS*, 114(13), 3521–3526.
- **Hinton, G. E., & Plaut, D. C. (1987).** Using fast weights to deblur old memories. *Proceedings of the Cognitive Science Society*.†
  Shows "savings": a network relearns forgotten associations much faster than
  it first learned them. This matters for reading KNOWLEDGE. In the pilot, the
  immortal learner explicitly kept only about 2 of 23 skills at the 90%
  readout threshold, yet stayed near 90% on the stream. So forgotten skills
  are probably relearned quickly, and KNOWLEDGE measures explicit retention,
  not recoverability.

## Motivation: AI self-replication

- The project was prompted by public reports and evaluations of AI systems
  replicating themselves. Before writing the introduction, add the specific
  report and the self-replication evaluation literature.
