# User Guide

## Show Users How To
- Generate reference motion.
- Use the runner to generate an `.onnx` for their motion.
- Run their `.onnx` in Mujoco Playground or a similar environment (if they do NOT have hardware) to 'play' with the droid before they build the real one and test their trained model.

---

## Find Resources for Their Droid
- STL models and instructions for variants.
- BOM pages.
- Cost calculator for each of the components and optional parts.
- If possible, provide Bambu X1 `.gcode` files to allow users to directly go from webpage to Bambu Labs to print the droid parts.

---

## Maintain and Update Their Droid
- Deploy the software onto the RPi or Jetson.
- Update ONNX models.
- Upload their own ONNX for variants that can be pulled by other users.
- Allow serial connection via Chrome/Edge's new method for USB connections to a webpage for updating where needed.
- OTA update for droids.

---

## Developer Section (Optional)
- A database of "serial numbers" that users can register their droids and a photo of them for the community.
- Allow users to upload a `.blend` file or `.usd` with an animation that runs through the training pipeline and produces a `.onnx` which can be shared.
- Eventually, once it matures a bit more, set up instructions for running gr00t / Newton for more autonomous droids.