//
//  InventoryView.swift
//  SaveAI
//
//  Created by Sam Kleiner on 3/1/25.
//

import SwiftUI

// Inventory Management
struct InventoryView: View {
    @StateObject private var productsViewModel = ProductsViewModel()
    
    var body: some View {
        NavigationView {
            List(productsViewModel.products) { product in
                VStack(alignment: .leading) {
                    Text(product.name)
                        .font(.headline)
                    Text("Stock: \(product.stockQuantity)")
                    Text("Price: \(product.formattedPrice)")
                }
            }
            .navigationTitle("Inventory")
            .onAppear {
                productsViewModel.fetchProducts()
            }
        }
    }
}
