import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import numpy as np

input_size = 1 
hidden_size = 128    
num_layers = 4      
output_size = 1 
epochs = 200

class BasicLSTM(nn.Module):
    def __init__(self):
        super(BasicLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)              # out: [batch, seq_len, hidden_size]
        out = self.fc(out[:, -1, :])
        return out

seq_len = 20
num_samples = 1000
x_vals = np.linspace(0, 100, num_samples)
data = x_vals * np.sin(x_vals)

# Prepare sequences
def make_sequences(data, seq_len):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len])
    return np.array(X), np.array(y)

X, y = make_sequences(data, seq_len)

X_tensor = torch.tensor(X, dtype=torch.float32).unsqueeze(-1)  # [samples, seq_len, 1]
y_tensor = torch.tensor(y, dtype=torch.float32).unsqueeze(-1)  # [samples, 1]

model = BasicLSTM()
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

losses = []

for epoch in range(epochs):
    model.train()
    output = model(X_tensor)
    loss = criterion(output, y_tensor)
    
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    losses.append(loss.item())
    
    if epoch % 10 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

# plot training loss
plt.figure(figsize=(6, 4))
plt.plot(losses, label="Training Loss")
plt.xlabel("Epoch")
plt.ylabel("MSE Loss")
plt.title("Loss Over Epochs")
plt.legend()
plt.grid(True)
plt.show()

model.eval()
with torch.no_grad():
    preds = model(X_tensor).squeeze().numpy()

plt.figure(figsize=(10, 4))
plt.plot(y, label="True", alpha=0.6)
plt.plot(preds, label="Predicted", alpha=0.6)
plt.title("True vs. LSTM Predictions")
plt.xlabel("Sample Index")
plt.ylabel("Value")
plt.legend()
plt.grid(True)
plt.show()