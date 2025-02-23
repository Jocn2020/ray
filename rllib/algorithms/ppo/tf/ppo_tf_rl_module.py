from typing import Any, Dict

from ray.rllib.algorithms.ppo.ppo_rl_module import PPORLModule
from ray.rllib.core.models.base import ACTOR, CRITIC
from ray.rllib.core.models.tf.encoder import ENCODER_OUT, STATE_OUT
from ray.rllib.core.rl_module.rl_module import RLModule
from ray.rllib.core.rl_module.tf.tf_rl_module import TfRLModule
from ray.rllib.policy.sample_batch import SampleBatch
from ray.rllib.utils.annotations import override
from ray.rllib.utils.framework import try_import_tf
from ray.rllib.utils.nested_dict import NestedDict

tf1, tf, _ = try_import_tf()


class PPOTfRLModule(TfRLModule, PPORLModule):
    framework: str = "tf2"

    @override(RLModule)
    def _forward_inference(self, batch: NestedDict) -> Dict[str, Any]:
        output = {}

        # Encoder forward pass.
        encoder_outs = self.encoder(batch)
        if STATE_OUT in encoder_outs:
            output[STATE_OUT] = encoder_outs[STATE_OUT]

        # Pi head.
        output[SampleBatch.ACTION_DIST_INPUTS] = self.pi(
            encoder_outs[ENCODER_OUT][ACTOR]
        )

        return output

    @override(RLModule)
    def _forward_exploration(self, batch: NestedDict) -> Dict[str, Any]:
        """PPO forward pass during exploration.

        Besides the action distribution, this method also returns the parameters of
        the policy distribution to be used for computing KL divergence between the old
        policy and the new policy during training.
        """
        output = {}

        # Shared encoder
        encoder_outs = self.encoder(batch)
        if STATE_OUT in encoder_outs:
            output[STATE_OUT] = encoder_outs[STATE_OUT]

        # Value head
        vf_out = self.vf(encoder_outs[ENCODER_OUT][CRITIC])
        output[SampleBatch.VF_PREDS] = tf.squeeze(vf_out, axis=-1)

        # Policy head
        action_logits = self.pi(encoder_outs[ENCODER_OUT][ACTOR])
        output[SampleBatch.ACTION_DIST_INPUTS] = action_logits

        return output

    @override(TfRLModule)
    def _forward_train(self, batch: NestedDict):
        output = {}

        # Shared encoder.
        encoder_outs = self.encoder(batch)
        if STATE_OUT in encoder_outs:
            output[STATE_OUT] = encoder_outs[STATE_OUT]

        # Value head.
        vf_out = self.vf(encoder_outs[ENCODER_OUT][CRITIC])
        # Squeeze out last dim (value function node).
        output[SampleBatch.VF_PREDS] = tf.squeeze(vf_out, axis=-1)

        # Policy head.
        action_logits = self.pi(encoder_outs[ENCODER_OUT][ACTOR])
        output[SampleBatch.ACTION_DIST_INPUTS] = action_logits

        return output
