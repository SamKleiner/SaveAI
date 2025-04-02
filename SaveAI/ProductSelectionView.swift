//
//  ProductSelectionView.swift
//  SaveAI
//
//  Created by Sam Kleiner on 3/1/25.
//

import SwiftUI

struct ProductSelectionView: View {
    @StateObject private var productsViewModel = ProductsViewModel()
    var onProductSelected: (Product) -> Void
    
    var body: some View {
        List(productsViewModel.products) { product in
            Button(action: {
                onProductSelected(product)
            }) {
                Text(product.name)
            }
        }
        .navigationTitle("Select Product")
        .onAppear {
            DispatchQueue.main.async {
                productsViewModel.fetchProducts()
            }
        }
    }
}
