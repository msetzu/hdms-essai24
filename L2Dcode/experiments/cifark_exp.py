import logging
import os
import pickle
import sys
import torch
import torch.optim as optim

sys.path.append("../")
import sys

import torch

sys.path.append("../")
import datetime

# allow logging to print everything
import logging
import argparse
from baselines.lce_surrogate import *
from datasetsdefer.synthetic_data import SyntheticData
from helpers.metrics import *
from networks.linear_net import *

logging.basicConfig(level=logging.DEBUG)
import torch.optim as optim
from baselines.compare_confidence import *
from baselines.differentiable_triage import *
from baselines.lce_surrogate import *
from baselines.mix_of_exps import *
from baselines.one_v_all import *
from baselines.selective_prediction import *
from datasetsdefer.broward import *
from datasetsdefer.chestxray import *
from datasetsdefer.cifar_h import *
from datasetsdefer.generic_dataset import *
from datasetsdefer.hatespeech import *
from datasetsdefer.imagenet_16h import *
from datasetsdefer.cifar_synth import *
from datasetsdefer.synthetic_data import *
from methods.milpdefer import *
from methods.realizable_surrogate import *
from networks.cnn import *
import datetime
from networks.cnn import NetSimple

def main():

    # check if there exists directory ../exp_data
    if not os.path.exists("../exp_data"):
        os.makedirs("../exp_data")
        os.makedirs("../exp_data/data")
        os.makedirs("../exp_data/plots")
    else:
        if not os.path.exists("../exp_data/data"):
            os.makedirs("../exp_data/data")
        if not os.path.exists("../exp_data/plots"):
            os.makedirs("../exp_data/plots")

    date_now = datetime.datetime.now()
    date_now = date_now.strftime("%Y-%m-%d_%H%M%S")

    ks =  [1, 2, 3, 4, 5, 6, 7, 8, 9]
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    optimizer = optim.Adam
    scheduler = None
    lr = 0.001
    max_trials = 10
    total_epochs = 50


    errors_lce = []
    errors_rs = []
    errors_one_v_all = []
    errors_selective = []
    errors_compare_confidence = []
    errors_differentiable_triage = []
    errors_mixofexps = []
    for trial in range(max_trials):
        errors_lce_trial = []
        errors_rs_trial = []
        errors_one_v_all_trial = []
        errors_selective_trial = []
        errors_compare_confidence_trial = []
        errors_differentiable_triage_trial = []
        errors_mixofexps_trial = []
        for expert_k in ks:
            # generate data
            dataset = CifarSynthDataset(expert_k, False, batch_size=512)

            model = NetSimple(11, 50, 50, 100, 20).to(device)
            RS = RealizableSurrogate(1, 300, model, device, True)
            RS.fit_hyperparam(
                dataset.data_train_loader,
                dataset.data_val_loader,
                dataset.data_test_loader,
                epochs=total_epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                verbose=False,
                test_interval=10,
            )
            rs_metrics = compute_deferral_metrics(RS.test(dataset.data_test_loader))

            model = NetSimple(11, 50, 50, 100, 20).to(device)
            mixofexps = MixtureOfExperts(model, device)
            mixofexps.fit(
                dataset.data_train_loader,
                dataset.data_val_loader,
                dataset.data_test_loader,
                epochs=total_epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                verbose=False,
                test_interval=10,
            )
            mixofexps_metrics = compute_deferral_metrics(
                mixofexps.test(dataset.data_test_loader)
            )

            model = NetSimple(11, 50, 50, 100, 20).to(device)
            LCE = LceSurrogate(1, 300, model, device)
            LCE.fit_hyperparam(
                dataset.data_train_loader,
                dataset.data_val_loader,
                dataset.data_test_loader,
                epochs=total_epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                verbose=False,
                test_interval=10,
            )
            lce_metrics = compute_deferral_metrics(LCE.test(dataset.data_test_loader))

            model_class = NetSimple(10, 50, 50, 100, 20).to(device)
            model_expert = NetSimple(2, 50, 50, 100, 20).to(device)
            compareconfidence = CompareConfidence(model_class, model_expert, device)
            compareconfidence.fit(
                dataset.data_train_loader,
                dataset.data_val_loader,
                dataset.data_test_loader,
                epochs=total_epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                verbose=False,
                test_interval=10,
            )
            compare_metrics = compute_deferral_metrics(
                compareconfidence.test(dataset.data_test_loader)
            )

            model = NetSimple(11, 50, 50, 100, 20).to(device)
            OVA = OVASurrogate(1, 300, model, device)
            OVA.fit(
                dataset.data_train_loader,
                dataset.data_val_loader,
                dataset.data_test_loader,
                epochs=total_epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                verbose=False,
                test_interval=10,
            )
            ova_metrics = compute_deferral_metrics(OVA.test(dataset.data_test_loader))

            model = NetSimple(10, 50, 50, 100, 20).to(device)
            SP = SelectivePrediction(model, device)
            SP.fit(
                dataset.data_train_loader,
                dataset.data_val_loader,
                dataset.data_test_loader,
                epochs=total_epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                verbose=False,
                test_interval=10,
            )
            sp_metrics = compute_deferral_metrics(SP.test(dataset.data_test_loader))

            model_class = NetSimple(10, 50, 50, 100, 20).to(device)
            model_rejector = NetSimple(2, 50, 50, 100, 20).to(device)
            diff_triage = DifferentiableTriage(
                model_class, model_rejector, device, 0.000, "human_error"
            )
            diff_triage.fit(
                dataset.data_train_loader,
                dataset.data_val_loader,
                dataset.data_test_loader,
                epochs=total_epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                verbose=False,
                test_interval=10,
            )
            diff_triage_metrics = compute_deferral_metrics(
                diff_triage.test(dataset.data_test_loader)
            )

            errors_mixofexps_trial.append(mixofexps_metrics)
            errors_lce_trial.append(lce_metrics)
            errors_rs_trial.append(rs_metrics)
            errors_one_v_all_trial.append(ova_metrics)
            errors_selective_trial.append(sp_metrics)
            errors_compare_confidence_trial.append(compare_metrics)
            errors_differentiable_triage_trial.append(diff_triage_metrics)
        errors_lce.append(errors_lce_trial)
        errors_rs.append(errors_rs_trial)
        errors_one_v_all.append(errors_one_v_all_trial)
        errors_selective.append(errors_selective_trial)
        errors_compare_confidence.append(errors_compare_confidence_trial)
        errors_differentiable_triage.append(errors_differentiable_triage_trial)
        errors_mixofexps.append(errors_mixofexps_trial)
        all_data = {
            "max_trials": max_trials,
            "ks": ks,
            "mixofexp": errors_mixofexps,
            "lce": errors_lce,
            "rs": errors_rs,
            "one_v_all": errors_one_v_all,
            "selective": errors_selective,
            "compare_confidence": errors_compare_confidence,
            "differentiable_triage": errors_differentiable_triage,
        }
        # dump data into pickle file
        with open("../exp_data/data/cifark_exp_" + date_now + ".pkl", "wb") as f:
            pickle.dump(all_data, f)


if __name__ == "__main__":
    main()
