# Training

## Dependencies

Install Tensorflow for python2.7 

``` bash
# For CPU
pip install tensorflow
# For GPU (nvidia)
pip install tensorflow-gpu
```
For more detailed instructions, you can follow [Tensorflow installation
instructions](https://www.tensorflow.org/install/).

You also have to have Tensorflow models, more info [here](https://github.com/tensorflow/models.git).

``` bash
git clone https://github.com/tensorflow/models.git
```

Once you have the models folder, follow these [installation instructions](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/installation.md).

## Training Setup

In w3p/training/ssd_mobilenet_v1_coco.config change paths for:
* Fine_tune_checkpoint
* Train_input_reader
* Eval_input_reader

When running for the first time, make sure checkpoint, model.ckpt* and graph.pbtxt are not in the training folder.

## Now you are ready to train

In w3p/object_detector_app/object_detection, run

``` bash
python train.py \
--logtostderr \
--pipeline_config_path=[path_to_directory]/w3p/training/ssd_mobilenet_v1_coco.config \
--train_dir=[path_to_directory]/w3p/training
```

During training, checkpoint, model.ckpt*, graph.pbtxt files will be created in the training directory.
These do not need to be added to git.

To test the model along with training, run the following concurrently 

``` bash
python eval.py \
--logtostderr \
--checkpoint_dir=[path_to_directory]/w3p/training \
--eval_dir=[path_to_directory]/w3p/training \
--pipeline_config_path=[path_to_directory]/w3p/training/ssd_mobilenet_v1_coco.config \
```

To use tensorboard, run

``` bash
tensorboard --logdir=[path_to_directory]/w3p/training
```

## Export model
``` bash
python [path_to_tf_models]/models/research/object_detection/export_inference_graph.py \
--input_type image_tensor \
--pipeline_config_path [path_to_w3p]/w3p/training/ssd_mobilenet_v1_coco.config \
--trained_checkpoint_prefix [path_to_model.ckpt ex: model.ckpt-200000]
--output_directory [name_of_directory_to_export_model ex: ssd_mobilenet_pitcher]
```

## File structure

This is the file structure in w3p:

- Training
	- Pitcher
	- ssd_mobilenet_v1_coco_2017_11_17/model.cpkt
	- Train.record
	- Test.record
	- Ssd_mobilenet_v1_coco.config
- Object_detector_app
	- Object_detection
		- Train.py
		- Trainer.py

