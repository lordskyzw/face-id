from deepface import DeepFace

result = DeepFace.verify("dataset/Tarmica/image_1c13626ce0d94befac4135b660308117.jpg", "dataset/Tarmica/image_327c4d2d253b4aca930138bacd8938ee.jpg")

print("Is verified: ", result["verified"])