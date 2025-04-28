//
//  AnalyticsView.swift
//  SaveAI
//
//  Created by Sam Kleiner on 3/1/25.
//

import SwiftUI

// Analytics and Sales Predictions
struct AnalyticsView: View {
    @StateObject private var predictionViewModel = PredictionViewModel()
    @State private var selectedProduct: Product?
    @State private var showPrediction = false
    
    var body: some View {
        NavigationView {
            VStack {
                if let product = selectedProduct {
                    Button("View Predictions for \(product.name)") {
                        predictionViewModel.getForecast(product: product)
                        predictionViewModel.getOptimalPrice(product: product)
                        showPrediction = true
                    }
                    .padding()
                    .sheet(isPresented: $showPrediction) {
                        PredictionDetailView(predictionViewModel: predictionViewModel, product: product)
                    }
                } else {
                    Text("Select a product to view predictions")
                }
                Spacer()
            }
            .navigationTitle("Analytics")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    NavigationLink("Select Product", destination: ProductSelectionView { product in
                        selectedProduct = product
                    })
                }
            }
        }
    }
}
