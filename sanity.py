from dataset import VimeoTripletDataset

dataset = VimeoTripletDataset(
    "/home/akshaygautam4451/Theia/data/vimeo_triplet_256",
    "/home/akshaygautam4451/Theia/splits/train_list.txt"
)

print(len(dataset))

x, y = dataset[0]

print(x.shape)
print(y.shape)
