

import wandb
wandb.init(
    project="theia-vfi",
    entity="YOUR_TEAM_NAME",
    name="basic_flow_v2",        # change for each new model version
    config={
        "model": "BasicFlowInterp",
        "batch_size": BATCH_SIZE,
        "epochs": EPOCHS,
        "lr": LR,
        "dataset": "Vimeo-90K",
    }
)



for epoch in range(num_epochs):


    train_loss = ...


    val_loss = ...
    val_psnr = ...
    val_ssim = ...

    wandb.log({
    "epoch":      epoch + 1,
    "train_loss": avg_train_loss,   # already exists in your train.py
    "val_loss":   avg_val_loss,     # already exists in your train.py
    "val_psnr":   avg_val_psnr,     # already exists in your train.py
    "val_ssim":   avg_val_ssim,     # already exists in your train.py
    "lr":         current_lr,       # already exists in your train.py
})


wandb.finish()