//
//  PredictionDetailView.swift
//  SaveAI
//
//  Created by Sam Kleiner on 3/1/25.
//

import SwiftUI

struct PredictionDetailView: View {
    @ObservedObject var predictionViewModel: PredictionViewModel
    let product: Product
    
    var body: some View {
        VStack {
            Text("Predictions for \(product.name)")
                .font(.headline)
                .padding()
            if let optimalPrice = predictionViewModel.optimalPrice,
               let predictedProfit = predictionViewModel.predictedProfit {
                Text("Optimal Price: $\(optimalPrice, specifier: "%.2f")")
                Text("Predicted Profit: $\(predictedProfit, specifier: "%.2f")")
            }
            List(predictionViewModel.predictions, id: \.id) { prediction in
                HStack {
                    Text(prediction.formattedDate)
                    Spacer()
                    Text("Qty: \(prediction.formattedQuantity)")
                }
            }
        }
        .padding()
    }
}
